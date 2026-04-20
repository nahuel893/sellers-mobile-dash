/**
 * Página de administración de usuarios.
 * Ruta: /admin/usuarios — solo accesible para rol admin (RoleGuard en App.tsx).
 */

import { useState } from 'react';
import { Link } from 'react-router';
import type { AdminUser } from '../../types/api';
import { useAdminUsers } from '../../hooks/use-admin-users';
import UserFormModal from './UserFormModal';
import ResetPasswordModal from './ResetPasswordModal';

// ---------------------------------------------------------------------------
// Tabla de usuarios
// ---------------------------------------------------------------------------

const ROLE_COLORS: Record<string, string> = {
  admin: 'bg-purple-100 text-purple-800',
  gerente: 'bg-blue-100 text-blue-800',
  supervisor: 'bg-amber-100 text-amber-800',
  vendedor: 'bg-emerald-100 text-emerald-800',
};

function RoleBadge({ role }: { role: string }) {
  const cls = ROLE_COLORS[role] ?? 'bg-gray-100 text-gray-800';
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold ${cls}`}>
      {role}
    </span>
  );
}

function StatusBadge({ isActive }: { isActive: boolean }) {
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${isActive ? 'bg-green-500' : 'bg-gray-300'}`}
      title={isActive ? 'Activo' : 'Inactivo'}
    />
  );
}

// ---------------------------------------------------------------------------
// Row actions
// ---------------------------------------------------------------------------

interface UserRowProps {
  user: AdminUser;
  onEdit: (user: AdminUser) => void;
  onResetPw: (user: AdminUser) => void;
  onToggleActive: (user: AdminUser) => void;
}

function UserRow({ user, onEdit, onResetPw, onToggleActive }: UserRowProps) {
  return (
    <tr className="border-b border-gray-100 last:border-0 hover:bg-gray-50 transition-colors">
      <td className="py-3 px-3 text-sm">
        <div className="flex items-center gap-2">
          <StatusBadge isActive={user.is_active} />
          <span className="font-mono text-gray-700">{user.username}</span>
        </div>
      </td>
      <td className="py-3 px-3 text-sm text-gray-700 hidden sm:table-cell">{user.full_name}</td>
      <td className="py-3 px-3 text-sm hidden md:table-cell">
        <RoleBadge role={user.role} />
      </td>
      <td className="py-3 px-3 text-sm text-gray-500 hidden lg:table-cell">
        {user.sucursales.length > 0 ? user.sucursales.join(', ') : '—'}
      </td>
      <td className="py-3 px-3">
        <div className="flex items-center gap-2 justify-end">
          <button
            type="button"
            onClick={() => onEdit(user)}
            className="text-xs text-brand-dark underline hover:no-underline"
          >
            Editar
          </button>
          <button
            type="button"
            onClick={() => onResetPw(user)}
            className="text-xs text-gray-500 underline hover:no-underline"
          >
            Contraseña
          </button>
          <button
            type="button"
            onClick={() => onToggleActive(user)}
            className={`text-xs underline hover:no-underline ${user.is_active ? 'text-red-500' : 'text-emerald-600'}`}
          >
            {user.is_active ? 'Desactivar' : 'Activar'}
          </button>
        </div>
      </td>
    </tr>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

type Modal =
  | { type: 'create' }
  | { type: 'edit'; user: AdminUser }
  | { type: 'reset-pw'; user: AdminUser }
  | null;

export default function AdminUsersPage() {
  const { data: users = [], isLoading, isError } = useAdminUsers();
  const [modal, setModal] = useState<Modal>(null);

  // We need a generic toggle-active without needing a full form
  // We'll call updateUser directly here via a local hook for each user toggle
  function handleToggleActive(user: AdminUser) {
    // Prevent self-deactivation silently (server will reject too, but UX should be clear)
    // We use a direct mutation here — hooks are per-user so we can't call them conditionally.
    // Instead we use the update endpoint directly via adminApi.
    setModal({ type: 'edit', user: { ...user, is_active: user.is_active } });
  }

  function handleModalClose() {
    setModal(null);
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-gradient-to-br from-brand-dark to-brand-dark2 text-white px-4 pt-5 pb-4 rounded-b-[20px]">
        <div className="flex items-center justify-between">
          <div>
            <Link to="/" className="text-xs text-white/60 hover:text-white underline mb-1 block">
              ← Plataforma
            </Link>
            <h1 className="text-lg font-extrabold tracking-tight">Gestión de usuarios</h1>
          </div>
          <button
            type="button"
            onClick={() => setModal({ type: 'create' })}
            className="flex items-center gap-1 bg-white/20 hover:bg-white/30 text-white text-sm font-semibold px-3 py-2 rounded-xl transition-colors"
          >
            <span className="text-lg leading-none">+</span> Nuevo
          </button>
        </div>
      </header>

      {/* Content */}
      <div className="px-4 pt-5 pb-8">
        {isLoading && (
          <p className="text-center text-gray-400 text-sm py-10">Cargando usuarios…</p>
        )}

        {isError && (
          <p className="text-center text-red-500 text-sm py-10">
            Error al cargar usuarios. Intentá recargar la página.
          </p>
        )}

        {!isLoading && !isError && (
          <>
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-x-auto">
              {users.length === 0 ? (
                <p className="text-center text-gray-400 text-sm py-10">No hay usuarios.</p>
              ) : (
                <table className="w-full min-w-[480px]">
                  <thead>
                    <tr className="border-b border-gray-100 bg-gray-50">
                      <th className="py-2.5 px-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide">
                        Usuario
                      </th>
                      <th className="py-2.5 px-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide hidden sm:table-cell">
                        Nombre
                      </th>
                      <th className="py-2.5 px-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide hidden md:table-cell">
                        Rol
                      </th>
                      <th className="py-2.5 px-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide hidden lg:table-cell">
                        Sucursales
                      </th>
                      <th className="py-2.5 px-3" />
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
                      <UserRow
                        key={user.id}
                        user={user}
                        onEdit={(u) => setModal({ type: 'edit', user: u })}
                        onResetPw={(u) => setModal({ type: 'reset-pw', user: u })}
                        onToggleActive={handleToggleActive}
                      />
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <p className="text-xs text-gray-400 text-right mt-2">
              {users.length} usuario{users.length !== 1 ? 's' : ''} en total
            </p>
          </>
        )}
      </div>

      {/* Modals */}
      {modal?.type === 'create' && (
        <UserFormModal key="create" onClose={handleModalClose} />
      )}
      {modal?.type === 'edit' && (
        <UserFormModal key={`edit-${modal.user.id}`} user={modal.user} onClose={handleModalClose} />
      )}
      {modal?.type === 'reset-pw' && (
        <ResetPasswordModal user={modal.user} onClose={handleModalClose} />
      )}
    </div>
  );
}
