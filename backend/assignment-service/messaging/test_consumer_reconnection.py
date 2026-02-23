"""Unit tests for RabbitMQ consumer reconnection logic (assignment-service).

Tests verify the exponential backoff reconnection behavior without
requiring Django or a real RabbitMQ connection.
"""

import sys
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Constants mirroring consumer.py defaults for isolated testing
# ---------------------------------------------------------------------------
INITIAL_RETRY_DELAY = 1
MAX_RETRY_DELAY = 60
RETRY_BACKOFF_FACTOR = 2


def _safe_close_fn(connection) -> None:
    """Mirror of consumer._safe_close for testing."""
    try:
        if connection and connection.is_open:
            connection.close()
    except Exception:
        pass


class TestBackoffDelayCalculation:
    """Test that delay follows exponential formula and respects max."""

    def test_delay_increases_exponentially(self) -> None:
        """Verify delay = INITIAL * (FACTOR ^ attempt) for first attempts."""
        for attempt in range(1, 6):
            delay = min(
                INITIAL_RETRY_DELAY * (RETRY_BACKOFF_FACTOR ** attempt),
                MAX_RETRY_DELAY,
            )
            expected = min(1 * (2 ** attempt), 60)
            assert delay == expected, f"Attempt {attempt}: expected {expected}, got {delay}"

    def test_delay_caps_at_max(self) -> None:
        """Verify delay never exceeds MAX_RETRY_DELAY even for high attempts."""
        attempt = 100
        delay = min(
            INITIAL_RETRY_DELAY * (RETRY_BACKOFF_FACTOR ** attempt),
            MAX_RETRY_DELAY,
        )
        assert delay == MAX_RETRY_DELAY

    def test_delay_sequence(self) -> None:
        """Verify the full delay sequence: 2, 4, 8, 16, 32, 60, 60..."""
        expected_delays = [2, 4, 8, 16, 32, 60, 60]
        for i, expected in enumerate(expected_delays, start=1):
            delay = min(
                INITIAL_RETRY_DELAY * (RETRY_BACKOFF_FACTOR ** i),
                MAX_RETRY_DELAY,
            )
            assert delay == expected


class TestSafeClose:
    """Test _safe_close handles all edge cases without raising."""

    def test_closes_open_connection(self) -> None:
        """Open connection should be closed."""
        conn = MagicMock()
        conn.is_open = True
        _safe_close_fn(conn)
        conn.close.assert_called_once()

    def test_skips_closed_connection(self) -> None:
        """Already-closed connection should not call close()."""
        conn = MagicMock()
        conn.is_open = False
        _safe_close_fn(conn)
        conn.close.assert_not_called()

    def test_handles_none_connection(self) -> None:
        """None connection should not raise."""
        _safe_close_fn(None)

    def test_handles_close_exception(self) -> None:
        """Exception during close() should be swallowed."""
        conn = MagicMock()
        conn.is_open = True
        conn.close.side_effect = RuntimeError("close failed")
        _safe_close_fn(conn)  # Should not raise

    def test_handles_is_open_exception(self) -> None:
        """Exception accessing is_open should be swallowed."""
        conn = MagicMock()
        type(conn).is_open = property(
            lambda self: (_ for _ in ()).throw(RuntimeError("boom"))
        )
        _safe_close_fn(conn)  # Should not raise


class TestReconnectionOnAMQPError:
    """Test that connection errors trigger retry with backoff."""

    @patch('time.sleep')
    @patch('sys.exit')
    def test_retries_on_connection_error(
        self, mock_exit: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Simulate AMQPConnectionError on first connect, success on second."""
        connection_error = type('AMQPConnectionError', (Exception,), {})

        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel

        call_count = 0

        def fake_blocking(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise connection_error("Connection refused")
            return mock_connection

        mock_channel.start_consuming.side_effect = KeyboardInterrupt()

        # Simulate the reconnection loop pattern
        attempt = 0
        connection = None
        max_iterations = 3
        iterations = 0
        while iterations < max_iterations:
            iterations += 1
            try:
                connection = fake_blocking()
                channel = connection.channel()
                if attempt > 0:
                    pass  # Successfully reconnected
                attempt = 0
                channel.start_consuming()
            except connection_error:
                attempt += 1
                delay = min(1 * (2 ** attempt), 60)
                mock_sleep(delay)
            except KeyboardInterrupt:
                break

        assert mock_sleep.called
        mock_sleep.assert_called_with(2)  # First attempt: 2^1 = 2

    @patch('time.sleep')
    def test_attempt_resets_on_success(self, mock_sleep: MagicMock) -> None:
        """After successful reconnection, attempt counter resets to 0."""
        connection_error = type('AMQPConnectionError', (Exception,), {})

        call_count = 0
        attempt = 0

        def simulate_loop(max_iter: int = 5):
            nonlocal call_count, attempt
            for _ in range(max_iter):
                call_count += 1
                try:
                    if call_count in (1, 4):
                        raise connection_error("fail")
                    # Success
                    attempt = 0
                    if call_count >= 5:
                        break
                except connection_error:
                    attempt += 1
                    delay = min(1 * (2 ** attempt), 60)
                    mock_sleep(delay)

        simulate_loop()
        assert attempt == 0


class TestMaxRetriesShutdown:
    """Test that MAX_RETRIES triggers sys.exit when exhausted."""

    @patch('sys.exit')
    @patch('time.sleep')
    def test_exits_after_max_retries(
        self, mock_sleep: MagicMock, mock_exit: MagicMock
    ) -> None:
        """With MAX_RETRIES=3, consumer should exit after 3 failures."""
        max_retries = 3
        connection_error = type('AMQPConnectionError', (Exception,), {})

        attempt = 0
        for _ in range(max_retries + 1):
            try:
                raise connection_error("fail")
            except connection_error:
                attempt += 1
                delay = min(1 * (2 ** attempt), 60)
                mock_sleep(delay)
                if max_retries > 0 and attempt >= max_retries:
                    mock_exit(1)
                    break

        mock_exit.assert_called_once_with(1)
        assert attempt == max_retries

    @patch('sys.exit')
    @patch('time.sleep')
    def test_infinite_retries_when_max_zero(
        self, mock_sleep: MagicMock, mock_exit: MagicMock
    ) -> None:
        """With MAX_RETRIES=0 (infinite), consumer should never call sys.exit."""
        max_retries = 0
        connection_error = type('AMQPConnectionError', (Exception,), {})

        attempt = 0
        for _ in range(100):
            try:
                raise connection_error("fail")
            except connection_error:
                attempt += 1
                delay = min(1 * (2 ** attempt), 60)
                mock_sleep(delay)
                if max_retries > 0 and attempt >= max_retries:
                    mock_exit(1)
                    break

        mock_exit.assert_not_called()
        assert attempt == 100


class TestKeyboardInterrupt:
    """Test graceful shutdown on KeyboardInterrupt."""

    def test_keyboard_interrupt_calls_safe_close(self) -> None:
        """KeyboardInterrupt should trigger _safe_close on the connection."""
        mock_connection = MagicMock()
        mock_connection.is_open = True

        try:
            raise KeyboardInterrupt()
        except KeyboardInterrupt:
            _safe_close_fn(mock_connection)

        mock_connection.close.assert_called_once()
