# claude-boilerplate

Моя база для Claude Code:
- общие правила работы: сначала обсуждаем, правила Karpathy для кода, отчёт после работы;
- выключенная AI-атрибуция в коммитах и PR;
- хук, который не даёт Claude коммитить и пушить в `main`.

## 1. Установка (один раз на компьютер)

```bash
git clone https://github.com/AlikhanSharapov01/boilerplate-setup-claude.git && cd boilerplate-setup-claude && ./setup.sh
# заранее посмотреть, что изменится (ничего не пишет): python3 scripts/install.py --global --dry-run
```

Скрипт кладёт в `~/.claude` файлы `CLAUDE.md`, `settings.json`, `hooks/guard-git.py` и `docs/`.
Перед изменением любой существующий файл копируется в `<файл>.bak-<дата>`. Твой
`settings.json` не затирается: новые настройки дописываются в него.

Проверка: команда должна вывести `Blocked by guard-git ...`, а затем `2`.

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"git push origin main"},"cwd":"'$PWD'"}' \
  | python3 ~/.claude/hooks/guard-git.py; echo $?
```

## 2. Новый проект

**Через Claude (удобнее).** Открой Claude Code в папке проекта и напиши «поставь базу в этот
проект». Skill `boilerplate-setup` посмотрит репо, заполнит `CLAUDE.md` реальными командами
(build/test/lint/sim) и покажет план. Записывать файлы он начнёт только после «давай».

**Руками.**

```bash
python3 scripts/install.py --project ~/path/to/repo
```

Эта команда кладёт в проект пустой шаблон `CLAUDE.md`, заполнить его нужно самому.

Если проект открываешь в Claude Code в браузере (claude.ai/code), добавь к команде `--guard`.
Там твой `~/.claude` не виден, поэтому хук нужно положить прямо в репо.

## 3. Что хук блокирует

| Блокирует | Не блокирует |
|---|---|
| commit / merge / rebase / reset / tag на `main`, `master`, `develop`, `production`, `release/*` | всё на feature-ветках, включая force-push |
| любой push в эти ветки, `push --all` | merge `main` в свою ветку |
| удаление или переименование этих веток | `git pull` на `main` |
| `gh pr merge`, `gh pr review --approve` | `gh pr create` |

Чтобы защитить в проекте ещё какие-то ветки, создай файл `.claude/protected-branches` и
впиши в него по одной ветке на строку, например `staging`.

## 4. Как менять базу

| Что хочешь поменять | Где | Потом |
|---|---|---|
| Общие правила | `global/CLAUDE.md` | `python3 scripts/install.py --global` |
| Правила одного проекта | `CLAUDE.md` в самом проекте | ничего |
| Хук | `global/hooks/guard-git.py` | `python3 scripts/test_guard.py`, затем `install.py --global` |

После любой правки в `global/` или `project/` запусти `python3 scripts/build_skill.py` и
попроси Claude обновить skill `boilerplate-setup`. Иначе skill продолжит ставить старую версию.

## Что где лежит

```
global/      то, что ставится в ~/.claude
project/     шаблон CLAUDE.md для проекта и settings.project.json (для --guard)
skill/       skill: SKILL.md собирается из SKILL.template.md; evals/ — тесты skill
scripts/     install.py, build_skill.py, test_guard.py
_old/        твои прежние CLAUDE.md и settings.json
```
