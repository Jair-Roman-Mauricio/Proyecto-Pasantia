import { useState, useEffect } from 'react';
import { Plus } from 'lucide-react';
import api from '../../config/api';
import type { User } from '../../types';
import Table from '../ui/Table';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import Modal from '../ui/Modal';
import Input from '../ui/Input';

export default function UserTable() {
  const [users, setUsers] = useState<User[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [form, setForm] = useState({ username: '', password: '', full_name: '', role: 'opersac', status: 'active' });

  useEffect(() => { loadUsers(); }, []);

  const loadUsers = async () => {
    const { data } = await api.get('/users');
    setUsers(data);
  };

  const handleSubmit = async () => {
    if (editingUser) {
      const update: Record<string, string> = {};
      if (form.full_name) update.full_name = form.full_name;
      if (form.status) update.status = form.status;
      if (form.password) update.password = form.password;
      await api.put(`/users/${editingUser.id}`, update);
    } else {
      await api.post('/users', form);
    }
    setShowForm(false);
    setEditingUser(null);
    setForm({ username: '', password: '', full_name: '', role: 'opersac', status: 'active' });
    loadUsers();
  };

  const openEdit = (u: User) => {
    setEditingUser(u);
    setForm({ username: u.username, password: '', full_name: u.full_name, role: u.role, status: u.status });
    setShowForm(true);
  };

  const statusColor = (s: string) => s === 'active' ? 'green' : s === 'inactive' ? 'gray' : 'red';

  const columns = [
    { key: 'id', header: 'ID' },
    { key: 'role', header: 'Rol', render: (u: User) => <Badge color={u.role === 'admin' ? 'green' : 'blue'}>{u.role}</Badge> },
    { key: 'full_name', header: 'Nombre' },
    { key: 'status', header: 'Estado', render: (u: User) => <Badge color={statusColor(u.status)}>{u.status}</Badge> },
    { key: 'actions', header: 'Acciones', render: (u: User) => <Button variant="ghost" size="sm" onClick={() => openEdit(u)}>Editar</Button> },
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

      <Modal isOpen={showForm} onClose={() => setShowForm(false)} title={editingUser ? 'Editar Usuario' : 'Nuevo Usuario'} size="md">
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
          <div className="flex gap-2 justify-end">
            <Button variant="secondary" onClick={() => setShowForm(false)}>Cancelar</Button>
            <Button onClick={handleSubmit}>{editingUser ? 'Guardar' : 'Crear'}</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
