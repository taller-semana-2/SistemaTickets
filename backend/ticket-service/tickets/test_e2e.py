import time
import psycopg2

from django.test import TestCase
from .serializer import TicketSerializer
from .views import TicketViewSet


class EndToEndTests(TestCase):
    def test_ticket_creation_triggers_assignment_in_assessment_service(self):
        """Crea un ticket (vía view.perform_create) y espera a que assignment-service
        procese el evento y guarde un registro en la base `assessment_db`.
        Este test asume que los contenedores `assessment-db`, `assessment-service`
        y `rabbitmq` están en ejecución y accesibles en la red de docker-compose.
        """

        # Crear ticket y publicar evento
        data = {"title": "E2E-T", "description": "end to end"}
        s = TicketSerializer(data=data)
        assert s.is_valid(), s.errors
        view = TicketViewSet()
        view.perform_create(s)
        ticket = s.instance

        # Conectar a la base de datos de assessment-service y esperar el registro
        conn_params = {
            'host': 'assessment-db',
            'port': 5432,
            'dbname': 'assessment_db',
            'user': 'assessment_user',
            'password': 'assessment_pass',
        }

        found = False
        deadline = time.time() + 15
        while time.time() < deadline and not found:
            try:
                conn = psycopg2.connect(**conn_params)
                cur = conn.cursor()
                cur.execute("SELECT ticket_id FROM assignments_ticketassignment WHERE ticket_id = %s", (str(ticket.id),))
                row = cur.fetchone()
                if row:
                    found = True
                cur.close()
                conn.close()
            except Exception:
                # DB might not be ready yet; sleep and retry
                time.sleep(0.5)

            if not found:
                time.sleep(0.5)

        self.assertTrue(found, "No se encontró la asignación en assessment_db dentro del timeout")
