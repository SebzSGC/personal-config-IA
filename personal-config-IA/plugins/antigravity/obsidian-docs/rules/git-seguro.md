---
trigger: model_decision
description: "Aplica estas reglas siempre que vayas a ejecutar comandos git (add, commit, push, pull, reset, rebase, checkout, restore, clean) en un repositorio de documentación o vault de Obsidian."
---

# Git seguro en la documentación

1. Usa el skill `git-documentacion` para commit, push y pull de la documentación.
2. Nunca ejecutes `git push --force`, `git reset --hard`, `git clean -f`, `git checkout -- .`, `git restore .` ni reescribas commits ya subidos sin que el usuario lo pida explícitamente después de explicarle qué se pierde. Para deshacer algo ya subido usa `git revert`.
3. Nunca uses `git add .` / `git add -A`: agrega rutas explícitas, un proyecto por commit.
4. Todo mensaje de commit sigue `tipo(proyecto): descripción` (tipos: feat, docs, fix, refactor, style, chore, revert), en minúscula, sin punto, ≤ 72 caracteres, con cuerpo "Qué cambió / Por qué" salvo cambios triviales.
5. Antes de `push`: `git pull --rebase`. Si el push es rechazado, repite pull --rebase; nunca fuerces.
6. No uses `--no-verify` para saltar los hooks salvo petición explícita del usuario.
7. Nunca escribas, pidas ni muestres contraseñas o tokens de git; el usuario inicia sesión cuando git lo solicite.
