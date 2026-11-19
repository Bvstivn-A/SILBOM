#!/usr/bin/env python3
"""Configura solamente variables SILBOM_DEMO_* en un .env local ignorado por Git.
Nunca imprime valores de contraseñas ni recibe contraseñas por argumentos.
"""
import argparse
import getpass
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile

KEYS = {
    'SILBOM_DEMO_TWO_USERS_ONLY': 'true',
    'SILBOM_DEMO_SUPERVISOR_USERNAME': 'supervisor',
    'SILBOM_DEMO_TECHNICIAN_USERNAME': 'tecnico',
}
PASSWORD_KEYS = ['SILBOM_DEMO_SUPERVISOR_PASSWORD', 'SILBOM_DEMO_TECHNICIAN_PASSWORD']

def validate_password(value):
    if len(value) < 12 or len(value.encode('utf-8')) > 72 or value.startswith('CAMBIAR_'):
        raise ValueError('La contraseña debe tener al menos 12 caracteres y hasta 72 bytes UTF-8.')
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError('La contraseña no puede contener saltos de línea ni caracteres de control.')

def configure(path, read_secret=getpass.getpass):
    path = Path(path).absolute()
    if path.is_symlink() or not path.is_file():
        raise ValueError('Primero prepara el .env local con la configuración existente de PostgreSQL y cifrado; no se creará ni reemplazará automáticamente.')
    check = subprocess.run(['git', 'check-ignore', '--quiet', '--', str(path)], cwd=path.parent, capture_output=True)
    tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', '--', str(path)], cwd=path.parent, capture_output=True)
    if check.returncode or tracked.returncode == 0:
        raise ValueError('El archivo debe estar ignorado por Git y no estar versionado.')
    original = path.read_bytes()
    lines = original.decode('utf-8').splitlines(keepends=True)
    positions = {}
    for i, line in enumerate(lines):
        match = re.match(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=(.*?)(?:\r?\n)?$', line)
        if match and match[1] in {*KEYS, *PASSWORD_KEYS}:
            if match[1] in positions:
                raise ValueError('Hay variables de demostración duplicadas. Revísalas localmente antes de continuar.')
            positions[match[1]] = (i, match[2])
    additions = dict(KEYS)
    for key in PASSWORD_KEYS:
        existing = positions.get(key)
        if existing and existing[1] and not existing[1].startswith('CAMBIAR_'):
            # Se conserva byte por byte cualquier secreto ya configurado.
            continue
        value = read_secret(f'{key} (entrada oculta): ')
        validate_password(value)
        if value != read_secret('Repite la contraseña (entrada oculta): '):
            raise ValueError('Las contraseñas no coinciden; el archivo no se modificó.')
        # Java Properties: no añadir comillas de shell; preservar barras y espacios iniciales.
        additions[key] = value.replace('\\', '\\\\').replace(' ', '\\ ')
    for key, value in additions.items():
        if key in positions:
            i, _ = positions[key]
            newline = '\r\n' if lines[i].endswith('\r\n') else '\n'
            lines[i] = f'{key}={value}{newline}'
        else:
            if lines and not lines[-1].endswith('\n'):
                lines[-1] += '\n'
            lines.append(f'{key}={value}\n')
    if path.read_bytes() != original:
        raise ValueError('El archivo cambió mientras se introducían los datos; no se sobrescribió.')
    fd, temporary = tempfile.mkstemp(prefix='.env.', dir=path.parent)
    try:
        os.fchmod(fd, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(fd, 'wb') as file:
            file.write(''.join(lines).encode('utf-8'))
            file.flush(); os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print('Variables de demostración configuradas. PostgreSQL y secretos existentes se conservaron. Archivo con permisos 0600; contraseñas no impresas.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archivo', type=Path, default=Path(__file__).resolve().parents[1] / '.env')
    args = parser.parse_args()
    try:
        configure(args.archivo)
    except (ValueError, OSError, UnicodeError) as error:
        # Los mensajes de validación no incluyen valores. Evitar OSError con contenido del archivo.
        parser.exit(1, str(error) + '\n' if isinstance(error, ValueError) else 'No se pudo configurar el archivo local; no se imprimieron sus contenidos.\n')

if __name__ == '__main__':
    main()
