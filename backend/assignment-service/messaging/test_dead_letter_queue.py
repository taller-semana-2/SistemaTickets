"""Unit tests for Dead Letter Queue (DLQ) support in the assignment-service consumer.

These tests verify that the RabbitMQ consumer properly configures a Dead Letter
Exchange (DLX) and Dead Letter Queue (DLQ) so that messages which fail processing
are not lost but routed to the DLQ for later inspection or reprocessing.

Acceptance Criteria (BUG-013):
    1. Main queue declared with ``x-dead-letter-exchange`` argument.
    2. Main queue declared with ``x-dead-letter-routing-key`` argument.
    3. A Dead Letter Exchange (DLX) is declared.
    4. A Dead Letter Queue (DLQ) is declared and bound to the DLX.
    5. Failed messages are nacked with ``requeue=False`` (routing to DLQ via DLX).

These tests are expected to FAIL until the DLQ implementation is added.
"""

import json
import sys
import types
import pytest
from unittest.mock import patch, MagicMock, ANY, call


# ---------------------------------------------------------------------------
# Environment defaults used by the consumer module
# ---------------------------------------------------------------------------
RABBIT_HOST = "localhost"
EXCHANGE_NAME = "ticket_events"
QUEUE_NAME = "assignment_queue"

# Expected DLQ naming conventions
DLX_EXCHANGE_NAME = f"{QUEUE_NAME}.dlx"
DLQ_QUEUE_NAME = f"{QUEUE_NAME}.dlq"
DLQ_ROUTING_KEY = f"{QUEUE_NAME}.dead-letter"


# ---------------------------------------------------------------------------
# Helper: import consumer with mocked Django / pika dependencies
# ---------------------------------------------------------------------------
def _build_mock_pika():
    """Create a mock pika module with real exception classes."""
    pika_mod = MagicMock()
    pika_mod.exceptions = types.SimpleNamespace(
        AMQPConnectionError=type("AMQPConnectionError", (Exception,), {}),
        StreamLostError=type("StreamLostError", (Exception,), {}),
        ConnectionClosedByBroker=type("ConnectionClosedByBroker", (Exception,), {}),
    )
    pika_mod.BlockingConnection = MagicMock()
    pika_mod.ConnectionParameters = MagicMock()
    return pika_mod


def _import_consumer_module():
    """Import the assignment consumer module with heavy deps mocked out.

    Returns:
        Tuple of (consumer_module, mock_pika, mock_channel) ready for assertions.
    """
    saved = {}
    mods_to_mock = [
        "django", "django.conf", "django.setup",
        "pika", "pika.exceptions",
        "assignments", "assignments.tasks",
        "assessment_service", "assessment_service.settings",
    ]

    for mod_name in mods_to_mock:
        saved[mod_name] = sys.modules.get(mod_name)
        sys.modules[mod_name] = MagicMock()

    mock_pika = _build_mock_pika()
    sys.modules["pika"] = mock_pika
    sys.modules["pika.exceptions"] = mock_pika.exceptions

    django_mock = MagicMock()
    django_mock.setup = MagicMock()
    sys.modules["django"] = django_mock

    # Remove cached consumer module to force re-import
    sys.modules.pop("messaging.consumer", None)
    sys.modules.pop("messaging", None)

    try:
        import importlib
        consumer = importlib.import_module("messaging.consumer")
        return consumer, mock_pika
    finally:
        # Restore original modules
        for mod_name, original in saved.items():
            if original is None:
                sys.modules.pop(mod_name, None)
            else:
                sys.modules[mod_name] = original


def _run_start_consuming_once(consumer, mock_pika):
    """Execute start_consuming, allowing it to connect once before stopping.

    Sets up the mock channel so that ``start_consuming`` raises
    ``KeyboardInterrupt`` to break out of the infinite loop after
    the first connection setup.

    Returns:
        mock_channel with all recorded calls for assertion.
    """
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel
    mock_pika.BlockingConnection.return_value = mock_connection

    # Break out of the loop after setup
    mock_channel.start_consuming.side_effect = KeyboardInterrupt()

    # Patch module-level constants needed by start_consuming
    consumer.RABBIT_HOST = RABBIT_HOST
    consumer.EXCHANGE_NAME = EXCHANGE_NAME
    consumer.QUEUE_NAME = QUEUE_NAME

    try:
        consumer.start_consuming()
    except KeyboardInterrupt:
        pass

    return mock_channel


# ---------------------------------------------------------------------------
# Tests: Queue declaration includes DLX arguments
# ---------------------------------------------------------------------------

class TestAssignmentQueueDeclaresDLXArguments:
    """Verify the main queue is declared with dead-letter routing arguments."""

    def test_queue_declares_dead_letter_exchange_argument(self) -> None:
        """Main queue must include x-dead-letter-exchange in its arguments."""
        consumer, mock_pika = _import_consumer_module()
        mock_channel = _run_start_consuming_once(consumer, mock_pika)

        # Find the queue_declare call for the main queue
        queue_declare_calls = mock_channel.queue_declare.call_args_list
        main_queue_call = None
        for c in queue_declare_calls:
            kwargs = c.kwargs if c.kwargs else {}
            args = c.args if c.args else ()
            queue_name = kwargs.get("queue") or (args[0] if args else None)
            if queue_name == QUEUE_NAME:
                main_queue_call = c
                break

        assert main_queue_call is not None, (
            f"queue_declare was never called for '{QUEUE_NAME}'"
        )

        # Check that arguments dict contains x-dead-letter-exchange
        kwargs = main_queue_call.kwargs if main_queue_call.kwargs else {}
        arguments = kwargs.get("arguments", {})
        assert "x-dead-letter-exchange" in arguments, (
            f"queue_declare for '{QUEUE_NAME}' missing 'x-dead-letter-exchange' argument. "
            f"Got arguments: {arguments}"
        )

    def test_queue_declares_dead_letter_routing_key_argument(self) -> None:
        """Main queue must include x-dead-letter-routing-key in its arguments."""
        consumer, mock_pika = _import_consumer_module()
        mock_channel = _run_start_consuming_once(consumer, mock_pika)

        queue_declare_calls = mock_channel.queue_declare.call_args_list
        main_queue_call = None
        for c in queue_declare_calls:
            kwargs = c.kwargs if c.kwargs else {}
            args = c.args if c.args else ()
            queue_name = kwargs.get("queue") or (args[0] if args else None)
            if queue_name == QUEUE_NAME:
                main_queue_call = c
                break

        assert main_queue_call is not None, (
            f"queue_declare was never called for '{QUEUE_NAME}'"
        )

        kwargs = main_queue_call.kwargs if main_queue_call.kwargs else {}
        arguments = kwargs.get("arguments", {})
        assert "x-dead-letter-routing-key" in arguments, (
            f"queue_declare for '{QUEUE_NAME}' missing 'x-dead-letter-routing-key' argument. "
            f"Got arguments: {arguments}"
        )


# ---------------------------------------------------------------------------
# Tests: DLX exchange is declared
# ---------------------------------------------------------------------------

class TestAssignmentDLXExchangeDeclared:
    """Verify a Dead Letter Exchange is explicitly declared."""

    def test_dlx_exchange_is_declared(self) -> None:
        """A dead-letter exchange must be declared via channel.exchange_declare."""
        consumer, mock_pika = _import_consumer_module()
        mock_channel = _run_start_consuming_once(consumer, mock_pika)

        exchange_declare_calls = mock_channel.exchange_declare.call_args_list
        dlx_declared = False
        for c in exchange_declare_calls:
            kwargs = c.kwargs if c.kwargs else {}
            args = c.args if c.args else ()
            exchange_name = kwargs.get("exchange") or (args[0] if args else None)
            # Accept any exchange name that is NOT the main fanout exchange
            # (it should be a dedicated DLX)
            if exchange_name and exchange_name != EXCHANGE_NAME:
                dlx_declared = True
                break

        assert dlx_declared, (
            "No Dead Letter Exchange was declared. "
            f"exchange_declare calls: {exchange_declare_calls}"
        )


# ---------------------------------------------------------------------------
# Tests: DLQ queue is declared and bound
# ---------------------------------------------------------------------------

class TestAssignmentDLQDeclaredAndBound:
    """Verify a Dead Letter Queue is declared and bound to the DLX."""

    def test_dlq_queue_is_declared(self) -> None:
        """A dead-letter queue must be declared via channel.queue_declare."""
        consumer, mock_pika = _import_consumer_module()
        mock_channel = _run_start_consuming_once(consumer, mock_pika)

        queue_declare_calls = mock_channel.queue_declare.call_args_list
        declared_queues = []
        for c in queue_declare_calls:
            kwargs = c.kwargs if c.kwargs else {}
            args = c.args if c.args else ()
            queue_name = kwargs.get("queue") or (args[0] if args else None)
            if queue_name:
                declared_queues.append(queue_name)

        # There must be at least 2 queues: the main queue and the DLQ
        non_main_queues = [q for q in declared_queues if q != QUEUE_NAME]
        assert len(non_main_queues) >= 1, (
            f"No Dead Letter Queue was declared. "
            f"Only found queues: {declared_queues}"
        )

    def test_dlq_queue_is_bound_to_dlx(self) -> None:
        """The DLQ must be bound to the DLX via channel.queue_bind."""
        consumer, mock_pika = _import_consumer_module()
        mock_channel = _run_start_consuming_once(consumer, mock_pika)

        queue_bind_calls = mock_channel.queue_bind.call_args_list
        # There should be a bind call that is NOT the main queue → main exchange
        non_main_binds = []
        for c in queue_bind_calls:
            kwargs = c.kwargs if c.kwargs else {}
            args = c.args if c.args else ()
            bound_exchange = kwargs.get("exchange") or (args[1] if len(args) > 1 else None)
            bound_queue = kwargs.get("queue") or (args[0] if args else None)
            if bound_exchange != EXCHANGE_NAME or bound_queue != QUEUE_NAME:
                non_main_binds.append(c)

        assert len(non_main_binds) >= 1, (
            "No queue_bind call found for the DLQ → DLX binding. "
            f"All queue_bind calls: {queue_bind_calls}"
        )


# ---------------------------------------------------------------------------
# Tests: Failed messages are nacked with requeue=False
# ---------------------------------------------------------------------------

class TestAssignmentFailedMessageNack:
    """Verify that processing failures result in nack(requeue=False)."""

    def test_failed_message_is_nacked_without_requeue(self) -> None:
        """When callback raises, message must be nacked with requeue=False."""
        consumer, mock_pika = _import_consumer_module()

        # Mock channel and method
        mock_ch = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = 42
        mock_properties = MagicMock()

        # Valid JSON body
        body = json.dumps({
            "event_type": "ticket.created",
            "ticket_id": 1,
            "title": "Test",
            "timestamp": "2026-01-01T00:00:00Z",
        }).encode()

        # Make the task processing raise an exception
        with patch.object(
            consumer, "process_ticket_event", create=True
        ) as mock_task:
            mock_delay = MagicMock(side_effect=Exception("Processing failed"))
            mock_task.delay = mock_delay

            consumer.callback(mock_ch, mock_method, mock_properties, body)

        # Verify nack was called with requeue=False
        mock_ch.basic_nack.assert_called_once_with(
            delivery_tag=42, requeue=False
        )

    def test_failed_message_is_not_acked(self) -> None:
        """When callback fails, basic_ack must NOT be called."""
        consumer, mock_pika = _import_consumer_module()

        mock_ch = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = 99
        mock_properties = MagicMock()

        body = json.dumps({
            "event_type": "ticket.created",
            "ticket_id": 2,
            "title": "Fail test",
            "timestamp": "2026-01-01T00:00:00Z",
        }).encode()

        with patch.object(
            consumer, "process_ticket_event", create=True
        ) as mock_task:
            mock_delay = MagicMock(side_effect=Exception("Boom"))
            mock_task.delay = mock_delay

            consumer.callback(mock_ch, mock_method, mock_properties, body)

        # On failure, ack should NOT have been called
        mock_ch.basic_ack.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: DLQ preserves original message content
# ---------------------------------------------------------------------------

class TestDLQPreservesMessageContent:
    """Verify that messages routed to DLQ maintain their original payload.

    This is inherently handled by RabbitMQ when using DLX, but we verify
    that nack(requeue=False) is used (not reject or discard) so the broker
    properly dead-letters the message with its original body intact.
    """

    def test_nack_without_requeue_preserves_content_via_dlx(self) -> None:
        """nack(requeue=False) on a queue with DLX args ensures content preservation."""
        consumer, mock_pika = _import_consumer_module()
        mock_channel = _run_start_consuming_once(consumer, mock_pika)

        # First, verify that DLX arguments are set (prerequisite)
        queue_declare_calls = mock_channel.queue_declare.call_args_list
        main_queue_call = None
        for c in queue_declare_calls:
            kwargs = c.kwargs if c.kwargs else {}
            args = c.args if c.args else ()
            queue_name = kwargs.get("queue") or (args[0] if args else None)
            if queue_name == QUEUE_NAME:
                main_queue_call = c
                break

        assert main_queue_call is not None, (
            f"queue_declare not called for '{QUEUE_NAME}'"
        )

        kwargs = main_queue_call.kwargs if main_queue_call.kwargs else {}
        arguments = kwargs.get("arguments", {})

        # Both DLX args must be present for content preservation via dead-lettering
        assert "x-dead-letter-exchange" in arguments, (
            "x-dead-letter-exchange must be set for DLQ content preservation"
        )
        assert "x-dead-letter-routing-key" in arguments, (
            "x-dead-letter-routing-key must be set for DLQ content preservation"
        )
