"""
Integration tests for DjangoTicketRepository.
Tests repository implementation with real Django ORM and database.

These tests validate the Repository pattern implementation and the translation
between domain entities and Django models.
"""

from django.test import TestCase
from datetime import datetime

from tickets.domain.entities import Ticket as DomainTicket
from tickets.infrastructure.repository import DjangoTicketRepository
from tickets.models import Ticket as DjangoTicket


class TestDjangoTicketRepositoryIntegration(TestCase):
    """Integration tests for DjangoTicketRepository with real database."""
    
    def setUp(self):
        """Set up repository instance for each test."""
        self.repository = DjangoTicketRepository()
    
    def tearDown(self):
        """Clean up database after each test."""
        DjangoTicket.objects.all().delete()
    
    # ==================== Save Operation Tests ====================
    
    def test_save_new_ticket_persists_to_database(self):
        """Test: Save new ticket creates record in database."""
        # Create domain entity using factory method
        ticket = DomainTicket.create(
            title="New Ticket",
            description="Test description"
        )
        
        # Save through repository
        saved_ticket = self.repository.save(ticket)
        
        # Verify ID was assigned
        assert saved_ticket.id is not None
        
        # Verify persistence in database
        django_ticket = DjangoTicket.objects.get(pk=saved_ticket.id)
        assert django_ticket.title == "New Ticket"
        assert django_ticket.description == "Test description"
        assert django_ticket.status == "OPEN"
        assert django_ticket.created_at is not None
    
    def test_save_existing_ticket_updates_database(self):
        """Test: Save existing ticket updates record in database."""
        # Create initial ticket in database
        django_ticket = DjangoTicket.objects.create(
            title="Original Title",
            description="Original Description",
            status="OPEN"
        )
        
        # Load as domain entity
        ticket = self.repository.find_by_id(django_ticket.id)
        
        # Modify entity
        ticket.change_status(DomainTicket.IN_PROGRESS)
        
        # Save changes
        self.repository.save(ticket)
        
        # Verify update in database
        django_ticket.refresh_from_db()
        assert django_ticket.status == "IN_PROGRESS"
        assert django_ticket.title == "Original Title"  # Unchanged
    
    def test_save_updates_only_specified_fields(self):
        """Test: Save only updates modified fields."""
        # Create ticket
        django_ticket = DjangoTicket.objects.create(
            title="Title",
            description="Description",
            status="OPEN"
        )
        original_created_at = django_ticket.created_at
        
        # Load and modify
        ticket = self.repository.find_by_id(django_ticket.id)
        ticket.change_status(DomainTicket.IN_PROGRESS)
        
        # Save
        self.repository.save(ticket)
        
        # Verify created_at unchanged (not in update_fields)
        django_ticket.refresh_from_db()
        assert django_ticket.created_at == original_created_at
        assert django_ticket.status == "IN_PROGRESS"
    
    def test_save_preserves_domain_entity_id(self):
        """Test: Save operation preserves entity ID reference."""
        ticket = DomainTicket.create(
            title="Test",
            description="Desc"
        )
        
        # Save and verify same object is updated
        saved_ticket = self.repository.save(ticket)
        assert saved_ticket is ticket
        assert ticket.id is not None
    
    # ==================== Find By ID Tests ====================
    
    def test_find_by_id_returns_domain_entity(self):
        """Test: Find by ID returns proper domain entity."""
        # Create ticket in database
        django_ticket = DjangoTicket.objects.create(
            title="Find Me",
            description="Test Find",
            status="IN_PROGRESS"
        )
        
        # Find through repository
        found_ticket = self.repository.find_by_id(django_ticket.id)
        
        # Verify domain entity
        assert isinstance(found_ticket, DomainTicket)
        assert found_ticket.id == django_ticket.id
        assert found_ticket.title == "Find Me"
        assert found_ticket.description == "Test Find"
        assert found_ticket.status == "IN_PROGRESS"
        assert found_ticket.created_at == django_ticket.created_at
    
    def test_find_by_id_returns_none_when_not_found(self):
        """Test: Find by ID returns None for non-existent ticket."""
        result = self.repository.find_by_id(99999)
        assert result is None
    
    def test_find_by_id_handles_deleted_ticket(self):
        """Test: Find by ID returns None after ticket is deleted."""
        # Create and delete
        django_ticket = DjangoTicket.objects.create(
            title="To Delete",
            description="Will be deleted",
            status="OPEN"
        )
        ticket_id = django_ticket.id
        django_ticket.delete()
        
        # Try to find
        result = self.repository.find_by_id(ticket_id)
        assert result is None
    
    # ==================== Find All Tests ====================
    
    def test_find_all_returns_all_tickets(self):
        """Test: Find all returns all tickets as domain entities."""
        # Create multiple tickets
        DjangoTicket.objects.create(title="T1", description="D1", status="OPEN")
        DjangoTicket.objects.create(title="T2", description="D2", status="IN_PROGRESS")
        DjangoTicket.objects.create(title="T3", description="D3", status="CLOSED")
        
        # Find all
        tickets = self.repository.find_all()
        
        # Verify
        assert len(tickets) == 3
        assert all(isinstance(t, DomainTicket) for t in tickets)
        titles = {t.title for t in tickets}
        assert titles == {"T1", "T2", "T3"}
    
    def test_find_all_returns_empty_list_when_no_tickets(self):
        """Test: Find all returns empty list when database is empty."""
        tickets = self.repository.find_all()
        assert tickets == []
    
    def test_find_all_orders_by_created_at_descending(self):
        """Test: Find all returns tickets ordered by creation date (newest first)."""
        # Create tickets (Django will set created_at automatically)
        t1 = DjangoTicket.objects.create(title="First", description="D1", status="OPEN")
        t2 = DjangoTicket.objects.create(title="Second", description="D2", status="OPEN")
        t3 = DjangoTicket.objects.create(title="Third", description="D3", status="OPEN")
        
        # Find all
        tickets = self.repository.find_all()
        
        # Verify order (newest first)
        assert tickets[0].id == t3.id
        assert tickets[1].id == t2.id
        assert tickets[2].id == t1.id
    
    # ==================== Delete Tests ====================
    
    def test_delete_removes_ticket_from_database(self):
        """Test: Delete removes ticket from database."""
        # Create ticket
        django_ticket = DjangoTicket.objects.create(
            title="To Delete",
            description="Will be removed",
            status="OPEN"
        )
        ticket_id = django_ticket.id
        
        # Delete through repository
        self.repository.delete(ticket_id)
        
        # Verify deletion
        exists = DjangoTicket.objects.filter(pk=ticket_id).exists()
        assert exists is False
    
    def test_delete_nonexistent_ticket_does_not_raise_error(self):
        """Test: Delete non-existent ticket does not raise error."""
        # Should not raise exception
        self.repository.delete(99999)
    
    def test_delete_does_not_affect_other_tickets(self):
        """Test: Delete only removes specified ticket."""
        # Create multiple tickets
        t1 = DjangoTicket.objects.create(title="T1", description="D1", status="OPEN")
        t2 = DjangoTicket.objects.create(title="T2", description="D2", status="OPEN")
        t3 = DjangoTicket.objects.create(title="T3", description="D3", status="OPEN")
        
        # Delete one
        self.repository.delete(t2.id)
        
        # Verify others remain
        assert DjangoTicket.objects.filter(pk=t1.id).exists()
        assert DjangoTicket.objects.filter(pk=t2.id).exists() is False
        assert DjangoTicket.objects.filter(pk=t3.id).exists()
    
    # ==================== Domain to Django Translation Tests ====================
    
    def test_to_django_model_creates_django_instance(self):
        """Test: to_django_model creates Django model instance."""
        # Create domain entity
        domain_ticket = DomainTicket(
            id=1,
            title="Test Title",
            description="Test Description",
            status=DomainTicket.OPEN,
            created_at=datetime.now()
        )
        
        # Convert to Django model
        django_ticket = self.repository.to_django_model(domain_ticket)
        
        # Verify Django instance
        assert isinstance(django_ticket, DjangoTicket)
        assert django_ticket.id == 1
        assert django_ticket.title == "Test Title"
        assert django_ticket.description == "Test Description"
        assert django_ticket.status == "OPEN"
    
    def test_to_django_model_fetches_existing_ticket(self):
        """Test: to_django_model fetches existing ticket from database."""
        # Create ticket in database
        existing = DjangoTicket.objects.create(
            title="Original",
            description="Original Desc",
            status="OPEN"
        )
        
        # Create domain entity with same ID but different values
        domain_ticket = self.repository.find_by_id(existing.id)
        domain_ticket.title = "Modified"
        domain_ticket.description = "Modified Desc"
        domain_ticket.change_status(DomainTicket.IN_PROGRESS)
        
        # Convert (should fetch and update)
        django_ticket = self.repository.to_django_model(domain_ticket)
        
        # Verify it's the same database instance
        assert django_ticket.pk == existing.pk
        # Verify values updated from domain entity
        assert django_ticket.title == "Modified"
        assert django_ticket.status == "IN_PROGRESS"
    
    def test_to_django_model_handles_nonexistent_id(self):
        """Test: to_django_model creates in-memory instance for non-existent ID."""
        # Create domain entity with non-existent ID using factory then modifying
        domain_ticket = DomainTicket.create(
            title="Test",
            description="Desc"
        )
        domain_ticket.id = 99999  # Manually set non-existent ID
        
        # Convert
        django_ticket = self.repository.to_django_model(domain_ticket)
        
        # Verify in-memory instance created
        assert django_ticket.id == 99999
        assert django_ticket.title == "Test"
    
    # ==================== Roundtrip Translation Tests ====================
    
    def test_save_and_find_roundtrip_preserves_data(self):
        """Test: Save and find preserve all ticket data."""
        # Create domain entity using factory
        original_ticket = DomainTicket.create(
            title="Roundtrip Test",
            description="Testing data preservation"
        )
        # Change to IN_PROGRESS for testing
        original_ticket.change_status(DomainTicket.IN_PROGRESS)
        
        # Save
        saved_ticket = self.repository.save(original_ticket)
        
        # Find
        found_ticket = self.repository.find_by_id(saved_ticket.id)
        
        # Verify all data preserved
        assert found_ticket.id == saved_ticket.id
        assert found_ticket.title == "Roundtrip Test"
        assert found_ticket.description == "Testing data preservation"
        assert found_ticket.status == "IN_PROGRESS"
        assert found_ticket.created_at is not None
    
    def test_multiple_saves_preserve_data_integrity(self):
        """Test: Multiple save operations maintain data integrity."""
        # Create and save using factory
        ticket = DomainTicket.create(
            title="Multi Save",
            description="Original"
        )
        self.repository.save(ticket)
        
        # Update and save again
        ticket.change_status(DomainTicket.IN_PROGRESS)
        self.repository.save(ticket)
        
        # Update and save once more
        ticket.change_status(DomainTicket.CLOSED)
        self.repository.save(ticket)
        
        # Find and verify final state
        final_ticket = self.repository.find_by_id(ticket.id)
        assert final_ticket.status == "CLOSED"
        assert final_ticket.title == "Multi Save"
        assert final_ticket.description == "Original"
    
    # ==================== Concurrent Access Tests ====================
    
    def test_repository_handles_concurrent_reads(self):
        """Test: Repository handles multiple concurrent reads safely."""
        # Create ticket
        django_ticket = DjangoTicket.objects.create(
            title="Concurrent",
            description="Test",
            status="OPEN"
        )
        
        # Perform multiple reads
        ticket1 = self.repository.find_by_id(django_ticket.id)
        ticket2 = self.repository.find_by_id(django_ticket.id)
        ticket3 = self.repository.find_by_id(django_ticket.id)
        
        # Verify independent entities
        assert ticket1 is not ticket2
        assert ticket2 is not ticket3
        assert ticket1.id == ticket2.id == ticket3.id
    
    def test_repository_isolates_entity_modifications(self):
        """Test: Modifications to one entity don't affect others."""
        # Create and find ticket twice
        django_ticket = DjangoTicket.objects.create(
            title="Isolation",
            description="Test",
            status="OPEN"
        )
        
        ticket1 = self.repository.find_by_id(django_ticket.id)
        ticket2 = self.repository.find_by_id(django_ticket.id)
        
        # Modify one entity
        ticket1.change_status(DomainTicket.IN_PROGRESS)
        
        # Verify other entity unchanged
        assert ticket2.status == "OPEN"
        assert ticket1.status == "IN_PROGRESS"
