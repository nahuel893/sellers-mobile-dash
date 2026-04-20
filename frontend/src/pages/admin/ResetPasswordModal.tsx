/**
 * Modal para resetear la contraseña de un usuario por parte del admin.
 */

import { useState } from 'react';
import type { AdminUser } from '../../types/api';
import { useResetPassword } from '../../hooks/use-admin-users';

interface ResetPasswordModalProps {
  user: AdminUser;
  onClose: () => void;
}

export default function ResetPasswordModal({ user, onClose }: ResetPasswordModalProps) {
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const reset = useResetPassword(user.id);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    try {
      await reset.mutateAsync({ password });
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al resetear contraseña');
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="reset-pw-title"
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 id="reset-pw-title" className="font-extrabold text-brand-dark text-base">
            Resetear contraseña
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

        <div className="px-5 py-4">
          {success ? (
            <div className="text-center py-4">
              <p className="text-green-700 font-semibold mb-1">¡Contraseña actualizada!</p>
              <p className="text-sm text-gray-500">
                La nueva contraseña fue establecida para <strong>{user.username}</strong>.
              </p>
              <button
                type="button"
                onClick={onClose}
                className="mt-4 w-full py-2.5 rounded-xl bg-brand-dark text-white text-sm font-semibold"
              >
                Cerrar
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <p className="text-sm text-gray-600">
                Establecer nueva contraseña para <strong>{user.username}</strong>.
              </p>

              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-base"
                placeholder="Nueva contraseña (mín. 6 caracteres)"
                autoComplete="new-password"
              />

              {error && (
                <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>
              )}

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-600 hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={reset.isPending}
                  className="flex-1 py-2.5 rounded-xl bg-brand-dark text-white text-sm font-semibold disabled:opacity-60"
                >
                  {reset.isPending ? 'Guardando…' : 'Guardar'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
