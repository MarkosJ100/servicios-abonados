import os
import sys
import unittest
from datetime import datetime, timedelta

# Ensure the current directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from app import Registro, User

class MigrationTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_registro_model_migration(self):
        """Test new Registro model attributes"""
        # Create a test registro
        test_registro = Registro(
            fecha=datetime.now().date(),
            numero_despacho='TEST-001',
            importe=100.50,
            nombre_compania='Test Company'
        )
        db.session.add(test_registro)
        db.session.commit()

        # Verify new attributes
        self.assertIsNotNone(test_registro.created_at, "created_at should be automatically set")
        self.assertIsNotNone(test_registro.updated_at, "updated_at should be automatically set")
        self.assertFalse(test_registro.is_deleted, "is_deleted should default to False")
        
        # Test mark_as_paid method
        test_registro.mark_as_paid(notas="Test payment")
        self.assertTrue(test_registro.pagado, "Record should be marked as paid")
        self.assertEqual(test_registro.estado, "Pagado", "Estado should be Pagado")
        self.assertEqual(test_registro.notas, "Test payment", "Notas should be set")

    def test_registro_query_methods(self):
        """Test new query methods"""
        # Create multiple test registros
        registros = [
            Registro(
                fecha=datetime.now().date() - timedelta(days=45),  # Overdue
                numero_despacho=f'TEST-{i}',
                importe=100.50 * i,
                nombre_compania='Test Company'
            ) for i in range(1, 4)
        ]
        db.session.add_all(registros)
        db.session.commit()

        # Test overdue payments
        overdue_payments = Registro.get_overdue_payments(days=30)
        self.assertEqual(len(overdue_payments), 3, "Should find overdue payments")

        # Test company summary
        summary = Registro.get_company_summary('Test Company')
        self.assertEqual(summary['total_registros'], 3, "Should have 3 total records")
        self.assertAlmostEqual(summary['total_importe'], 100.50 * 6, places=2, msg="Total importe should be correct")

    def test_soft_delete(self):
        """Test soft delete functionality"""
        test_registro = Registro(
            fecha=datetime.now().date(),
            numero_despacho='TEST-SOFT-DELETE',
            importe=200.75,
            nombre_compania='Soft Delete Company'
        )
        db.session.add(test_registro)
        db.session.commit()

        # Soft delete the registro
        test_registro.soft_delete()
        
        # Verify soft delete
        self.assertTrue(test_registro.is_deleted, "Record should be marked as deleted")
        
        # Verify it's excluded from queries
        active_registros = Registro.query.filter(Registro.is_deleted == False).all()
        self.assertNotIn(test_registro, active_registros, "Soft deleted record should not appear in active records")

if __name__ == '__main__':
    unittest.main()
