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

const emptyForm = { username: '', password: '', full_name: '', role: 'opersac', status: 'active', email: '', phone: '' };

export default function UserTable() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [formError, setFormError] = useState('');
  const [loading, setLoading] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<User | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  useEffect(() => { loadUsers(); }, []);

  const loadUsers = async () => {
    try {
      const { data } = await api.get('/users');
      setUsers(data);
    } catch {
      /* silencio — el error se muestra en la tabla vacía */
    }
  };

  const handleSubmit = async () => {
    if (!editingUser && (!form.username.trim() || !form.password.trim() || !form.full_name.trim())) {
      setFormError('Usuario, contraseña y nombre son obligatorios.');
      return;
    }
    if (editingUser && !form.full_name.trim()) {
      setFormError('El nombre no puede estar vacío.');
      return;
    }
    setFormError('');
    setLoading(true);
    try {
      if (editingUser) {
        const update: Record<string, string> = {};
        if (form.full_name) update.full_name = form.full_name;
        if (form.status)    update.status    = form.status;
        if (form.password)  update.password  = form.password;
        if (form.email)     update.email     = form.email;
        if (form.phone)     update.phone     = form.phone;
        await api.put(`/users/${editingUser.id}`, update);
      } else {
        await api.post('/users', {
          username:  form.username,
          password:  form.password,
          full_name: form.full_name,
          role:      form.role,
          email:     form.email  || undefined,
          phone:     form.phone  || undefined,
        });
      }
      setShowForm(false);
      setEditingUser(null);
      setForm(emptyForm);
      loadUsers();
    } catch (err: any) {
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
    setForm({ ...emptyForm, username: u.username, full_name: u.full_name, role: u.role, status: u.status });
    setFormError('');
    setShowForm(true);
  };

  const openNew = () => {
    setEditingUser(null);
    setForm(emptyForm);
    setFormError('');
    setShowForm(true);
  };

  const statusColor = (s: string) => s === 'active' ? 'green' : s === 'inactive' ? 'gray' : 'red';
  const roleColor   = (r: string) => r === 'admin' ? 'green' : 'blue';

  const columns = [
    { key: 'username',  header: 'Usuario',  render: (u: User) => <span className="font-mono text-sm">{u.username}</span> },
    { key: 'full_name', header: 'Nombre' },
    { key: 'role',   header: 'Rol',    render: (u: User) => <Badge color={roleColor(u.role)}>{u.role}</Badge> },
    { key: 'status', header: 'Estado', render: (u: User) => <Badge color={statusColor(u.status)}>{u.status}</Badge>, className: 'hidden sm:table-cell' },
    {
      key: 'actions', header: 'Acciones',
      render: (u: User) => (
        <div className="flex gap-2 items-center">
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
        <Button size="sm" onClick={openNew}>
          <Plus size={16} className="mr-1" /> Nuevo Usuario
        </Button>
      </div>

      <Table columns={columns} data={users} rowKey={(u) => u.id} />

      {/* Modal crear / editar */}
      <Modal
        isOpen={showForm}
        onClose={() => { setShowForm(false); setFormError(''); }}
        title={editingUser ? `Editar — ${editingUser.username}` : 'Nuevo Usuario'}
        size="md"
      >
        <div className="space-y-4">
          {/* Rol: solo al crear */}
          {!editingUser && (
            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Rol *</label>
              <div className="flex gap-3">
                {(['opersac', 'admin'] as const).map((r) => (
                  <button
                    key={r}
                    type="button"
                    onClick={() => setForm({ ...form, role: r })}
                    className={`flex-1 py-2 rounded-lg border text-sm font-medium transition-colors
                      ${form.role === r
                        ? r === 'admin'
                          ? 'border-green-500 bg-green-500/10 text-green-400'
                          : 'border-blue-500 bg-blue-500/10 text-blue-400'
                        : 'border-[var(--border-color)] text-[var(--text-muted)] hover:border-[var(--text-muted)]'
                      }`}
                  >
                    {r === 'admin' ? 'Administrador' : 'Operador SAC'}
                  </button>
                ))}
              </div>
            </div>
          )}

          {!editingUser && (
            <Input
              label="Usuario *"
              placeholder="ej. jperez"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
            />
          )}

          <Input
            label="Nombre Completo *"
            placeholder="ej. Juan Pérez"
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          />

          <Input
            label={editingUser ? 'Nueva Contraseña (dejar vacío para no cambiar)' : 'Contraseña *'}
            type="password"
            placeholder={editingUser ? '••••••••' : 'Mínimo 6 caracteres'}
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Correo (opcional)"
              type="email"
              placeholder="correo@empresa.pe"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
            <Input
              label="Teléfono (opcional)"
              placeholder="999 000 000"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
            />
          </div>

          {/* Estado: solo al editar */}
          {editingUser && (
            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Estado</label>
              <select
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)]"
              >
                <option value="active">Activo</option>
                <option value="inactive">Inactivo</option>
                <option value="reported">Reportado</option>
              </select>
            </div>
          )}

          {formError && (
            <p className="text-sm text-red-500 bg-red-500/10 rounded-lg px-3 py-2">{formError}</p>
          )}

          <div className="flex gap-2 justify-end pt-1">
            <Button variant="secondary" onClick={() => { setShowForm(false); setFormError(''); }}>
              Cancelar
            </Button>
            <Button onClick={handleSubmit} disabled={loading}>
              {loading ? 'Guardando...' : editingUser ? 'Guardar cambios' : 'Crear usuario'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal confirmación eliminar */}
      <Modal
        isOpen={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        title="Eliminar usuario"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-sm text-[var(--text-secondary)]">
            ¿Eliminar a <strong className="text-[var(--text-primary)]">{deleteTarget?.full_name}</strong>{' '}
            (<span className="font-mono">{deleteTarget?.username}</span>)? Esta acción no se puede deshacer.
          </p>
          <div className="flex gap-2 justify-end">
            <Button variant="secondary" onClick={() => setDeleteTarget(null)}>Cancelar</Button>
            <Button
              onClick={handleDelete}
              disabled={deleteLoading}
              className="bg-red-500 hover:bg-red-600 text-white"
            >
              {deleteLoading ? 'Eliminando...' : 'Eliminar'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
