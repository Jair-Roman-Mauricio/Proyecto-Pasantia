import { useState, useEffect } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import api from '../../config/api';
import type { User } from '../../types';
import { useAuth } from '../../context/AuthContext';
import Table from '../ui/Table';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import Modal from '../ui/Modal';
import Input from '../ui/Input';

export default function UserTable() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [form, setForm] = useState({ username: '', password: '', full_name: '', role: 'opersac', status: 'active' });
  const [formError, setFormError] = useState('');
  const [loading, setLoading] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<User | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  useEffect(() => { loadUsers(); }, []);

  const loadUsers = async () => {
    const { data } = await api.get('/users');
    setUsers(data);
  };

  const handleSubmit = async () => {
    // Validación básica de campos obligatorios antes de enviar
    if (!editingUser && (!form.username.trim() || !form.password.trim() || !form.full_name.trim())) {
      setFormError('Completa todos los campos obligatorios.');
      return;
    }
    setFormError('');
    setLoading(true);
    try {
      if (editingUser) {
        const update: Record<string, string> = {};
        if (form.full_name) update.full_name = form.full_name;
        if (form.status) update.status = form.status;
        if (form.password) update.password = form.password;
        await api.put(`/users/${editingUser.id}`, update);
      } else {
        await api.post('/users', { username: form.username, password: form.password, full_name: form.full_name, role: form.role });
      }
      setShowForm(false);
      setEditingUser(null);
      setForm({ username: '', password: '', full_name: '', role: 'opersac', status: 'active' });
      loadUsers();
    } catch (err: any) {
      // Muestra el mensaje de error del backend (ej: "El nombre de usuario ya existe")
      const detail = err?.response?.data?.detail;
      setFormError(detail ?? 'Error al guardar. Intente nuevamente.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      await api.delete(`/users/${deleteTarget.id}`);
      setDeleteTarget(null);
      loadUsers();
    } catch (err: any) {
      alert(err?.response?.data?.detail ?? 'Error al eliminar el usuario.');
    } finally {
      setDeleteLoading(false);
    }
  };

  const openEdit = (u: User) => {
    setEditingUser(u);
    setForm({ username: u.username, password: '', full_name: u.full_name, role: u.role, status: u.status });
    setShowForm(true);
  };

  const statusColor = (s: string) => s === 'active' ? 'green' : s === 'inactive' ? 'gray' : 'red';

  const columns = [
    { key: 'id', header: 'ID', className: 'hidden sm:table-cell' },
    { key: 'role', header: 'Rol', render: (u: User) => <Badge color={u.role === 'admin' ? 'green' : 'blue'}>{u.role}</Badge> },
    { key: 'full_name', header: 'Nombre' },
    { key: 'status', header: 'Estado', render: (u: User) => <Badge color={statusColor(u.status)}>{u.status}</Badge>, className: 'hidden sm:table-cell' },
    {
      key: 'actions', header: 'Acciones',
      render: (u: User) => (
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={() => openEdit(u)}>Editar</Button>
          {u.id !== currentUser?.id && (
            <button
              onClick={() => setDeleteTarget(u)}
              title="Eliminar usuario"
              className="p-1.5 rounded hover:bg-red-500/10 text-[var(--text-muted)] hover:text-red-500 transition-colors"
            >
              <Trash2 size={15} />
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-[var(--text-primary)]">Gestion de Usuarios</h2>
        <Button size="sm" onClick={() => { setEditingUser(null); setForm({ username: '', password: '', full_name: '', role: 'opersac', status: 'active' }); setShowForm(true); }}>
          <Plus size={16} className="mr-1" /> Nuevo Usuario
        </Button>
      </div>
      <Table columns={columns} data={users} rowKey={(u) => u.id} />

      <Modal isOpen={showForm} onClose={() => { setShowForm(false); setFormError(''); }} title={editingUser ? 'Editar Usuario' : 'Nuevo Usuario'} size="md">
        <div className="space-y-4">
          {!editingUser && <Input label="Usuario" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />}
          <Input label="Nombre Completo" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
          <Input label={editingUser ? 'Nueva Contrasena (opcional)' : 'Contrasena'} type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          {!editingUser && (
            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Rol</label>
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} className="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)]">
                <option value="admin">Admin</option>
                <option value="opersac">Opersac</option>
              </select>
            </div>
          )}
          {editingUser && (
            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Estado</label>
              <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} className="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)]">
                <option value="active">Activo</option>
                <option value="inactive">Inactivo</option>
                <option value="reported">Reportado</option>
              </select>
            </div>
          )}
          {/* Mensaje de error visible dentro del modal */}
          {formError && <p className="text-sm text-red-500">{formError}</p>}
          <div className="flex gap-2 justify-end">
            <Button variant="secondary" onClick={() => { setShowForm(false); setFormError(''); }}>Cancelar</Button>
            <Button onClick={handleSubmit} disabled={loading}>{loading ? 'Guardando...' : editingUser ? 'Guardar' : 'Crear'}</Button>
          </div>
        </div>
      </Modal>
      {/* Modal de confirmación de eliminación */}
      <Modal isOpen={deleteTarget !== null} onClose={() => setDeleteTarget(null)} title="Eliminar usuario" size="sm">
        <div className="space-y-4">
          <p className="text-sm text-[var(--text-secondary)]">
            ¿Estás seguro de que deseas eliminar al usuario <strong className="text-[var(--text-primary)]">{deleteTarget?.full_name}</strong> ({deleteTarget?.username})? Esta acción no se puede deshacer.
          </p>
          <div className="flex gap-2 justify-end">
            <Button variant="secondary" onClick={() => setDeleteTarget(null)}>Cancelar</Button>
            <Button onClick={handleDelete} disabled={deleteLoading} className="bg-red-500 hover:bg-red-600 text-white">
              {deleteLoading ? 'Eliminando...' : 'Eliminar'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
