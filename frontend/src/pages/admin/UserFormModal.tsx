/**
 * Modal para crear o editar un usuario.
 * Se usa tanto en modo "crear" (sin user prop) como "editar" (con user prop).
 */

import { useState } from 'react';
import type { AdminUser, Role } from '../../types/api';
import { useAdminRoles, useAdminSucursales, useCreateUser, useUpdateUser } from '../../hooks/use-admin-users';

interface UserFormModalProps {
  /** Si se pasa, el modal está en modo edición. */
  user?: AdminUser;
  onClose: () => void;
}

/**
 * UserFormModal — crea o edita un usuario.
 * Se monta con key={user?.id} desde el padre para que React desmonte
 * y remonte cuando cambia el usuario, reiniciando el estado del form.
 */
export default function UserFormModal({ user, onClose }: UserFormModalProps) {
  const isEditing = user !== undefined;

  const { data: roles = [] } = useAdminRoles();
  const { data: sucursales = [] } = useAdminSucursales();

  const createUser = useCreateUser();
  const updateUser = useUpdateUser(user?.id ?? 0);

  const [form, setForm] = useState({
    username: user?.username ?? '',
    full_name: user?.full_name ?? '',
    role: user?.role ?? 'vendedor',
    is_active: user?.is_active ?? true,
    password: '',
    sucursales: user?.sucursales ?? [] as number[],
  });
  const [error, setError] = useState<string | null>(null);

  function handleSucursalToggle(id: number) {
    setForm((prev) => ({
      ...prev,
      sucursales: prev.sucursales.includes(id)
        ? prev.sucursales.filter((s) => s !== id)
        : [...prev.sucursales, id],
    }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    try {
      if (isEditing) {
        await updateUser.mutateAsync({
          full_name: form.full_name,
          role: form.role as AdminUser['role'],
          is_active: form.is_active,
          sucursales: form.sucursales,
        });
      } else {
        if (!form.password) {
          setError('La contraseña es obligatoria.');
          return;
        }
        await createUser.mutateAsync({
          username: form.username,
          password: form.password,
          full_name: form.full_name,
          role: form.role as AdminUser['role'],
          sucursales: form.sucursales,
        });
      }
      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error desconocido';
      setError(message);
    }
  }

  const isPending = createUser.isPending || updateUser.isPending;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 id="modal-title" className="font-extrabold text-brand-dark text-base">
            {isEditing ? 'Editar usuario' : 'Nuevo usuario'}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
            aria-label="Cerrar"
          >
            ×
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-5 py-4 flex flex-col gap-4">
          {/* Username — solo editable al crear */}
          <Field label="Usuario">
            <input
              type="text"
              required
              disabled={isEditing}
              value={form.username}
              onChange={(e) => setForm((p) => ({ ...p, username: e.target.value }))}
              className="input-base disabled:bg-gray-50 disabled:text-gray-400"
              placeholder="nombre_usuario"
              autoComplete="off"
            />
          </Field>

          {/* Nombre completo */}
          <Field label="Nombre completo">
            <input
              type="text"
              required
              value={form.full_name}
              onChange={(e) => setForm((p) => ({ ...p, full_name: e.target.value }))}
              className="input-base"
              placeholder="Juan Pérez"
            />
          </Field>

          {/* Password — solo al crear */}
          {!isEditing && (
            <Field label="Contraseña">
              <input
                type="password"
                required
                minLength={6}
                value={form.password}
                onChange={(e) => setForm((p) => ({ ...p, password: e.target.value }))}
                className="input-base"
                placeholder="Mínimo 6 caracteres"
                autoComplete="new-password"
              />
            </Field>
          )}

          {/* Rol */}
          <Field label="Rol">
            <select
              value={form.role}
              onChange={(e) => setForm((p) => ({ ...p, role: e.target.value as Role }))}
              className="input-base"
            >
              {roles.map((r) => (
                <option key={r.id} value={r.name}>
                  {r.name}
                </option>
              ))}
            </select>
          </Field>

          {/* Estado — solo al editar */}
          {isEditing && (
            <Field label="Estado">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(e) => setForm((p) => ({ ...p, is_active: e.target.checked }))}
                  className="w-4 h-4 accent-brand-dark"
                />
                <span className="text-sm text-gray-700">Activo</span>
              </label>
            </Field>
          )}

          {/* Sucursales */}
          {sucursales.length > 0 && (
            <Field label="Sucursales">
              <div className="flex flex-col gap-1 max-h-36 overflow-y-auto border border-gray-200 rounded-lg p-2">
                {sucursales.map((s) => (
                  <label key={s.id} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={form.sucursales.includes(s.id)}
                      onChange={() => handleSucursalToggle(s.id)}
                      className="w-4 h-4 accent-brand-dark"
                    />
                    <span className="text-sm text-gray-700">{s.descripcion}</span>
                  </label>
                ))}
              </div>
            </Field>
          )}

          {/* Error */}
          {error && (
            <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isPending}
              className="flex-1 py-2.5 rounded-xl bg-brand-dark text-white text-sm font-semibold hover:bg-brand-dark2 transition-colors disabled:opacity-60"
            >
              {isPending ? 'Guardando…' : isEditing ? 'Guardar cambios' : 'Crear usuario'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{label}</label>
      {children}
    </div>
  );
}
