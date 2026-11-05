# Локальные зависимости HVCO

`dependencies.json` фиксирует два внешних источника по полному Git SHA; поля записи — `name`, `url`, `revision`, `files`, `purpose`.

`prompt-audience-research` даёт контракт единой базы знаний: клиент мечты, портрет и Big Idea, CustDev, распаковка смыслов и STP.

CustDev здесь включает симуляцию: её результаты нельзя выдавать за реальные интервью.

Это источник формата исследования, а не runtime или API HVCO; дополнительных GitHub-зависимостей в проверенном audience-research не выявлено.

`promt-copywriting` предоставляет только опциональный локальный журнал `scripts/loop.py` и его справку `docs/loop-tool.md`.

HVCO не заимствует его авторский голос, workflow или персону Васьки: стиль, роли и принятие результата определяются [workflow HVCO](../workflow.md).

Для ручного процесса соседние клоны необязательны; для использования журнала нужен `promt-copywriting` на указанной ревизии.

Проверка checkout не подтверждает достоверность клиентского исследования и не выполняет содержательные проверки текста.

## Подготовка checkout

Из общего каталога, содержащего `promt-hvco`, выполните команды ниже, только если соответствующего клона ещё нет.

```sh
git clone https://github.com/BermanRoman/prompt-audience-research.git prompt-audience-research
git -C prompt-audience-research checkout --detach d9959823dcd659b03c2527498310b0ba266db1f1
git -C prompt-audience-research rev-parse HEAD
git -C prompt-audience-research status --short --untracked-files=all

git clone https://github.com/BermanRoman/promt-copywriting.git promt-copywriting
git -C promt-copywriting checkout --detach bb091b6003f836106d09ed2bd5e91a8fb5d961dd
git -C promt-copywriting rev-parse HEAD
git -C promt-copywriting status --short --untracked-files=all
```

Каждый `rev-parse` должен вывести указанный SHA, каждый `status` — пустой результат.

Для уже существующего клона сначала проверьте HEAD и статус; не переключайте ревизию поверх чужих изменений.

## Проверка

Из корня HVCO:

```sh
python3 scripts/check_dependencies.py
python3 scripts/check_dependencies.py --root /path/to/common-parent
python3 -m unittest discover -s tests -p 'test_dependencies.py' -v
```

Нужны Python 3.9+ и Git; дополнительных Python-пакетов нет.

`--root` всегда означает каталог, непосредственно содержащий checkout’ы `prompt-audience-research/` и `promt-copywriting/`, а не путь к HVCO или отдельной зависимости.

Относительный `--root` считается от текущего рабочего каталога; значение по умолчанию — родитель каталога HVCO независимо от места запуска скрипта.

Скрипт проверяет оба checkout’а: корень Git-репозитория, точное совпадение HEAD, наличие файлов внутри checkout и отсутствие отслеживаемых либо неотслеживаемых изменений.

Игнорируемые Git файлы, например заранее исключённые `runs/`, не мешают проверке.

Коды завершения: `0` — всё совпало, `1` — отсутствующая, устаревшая или изменённая зависимость, `2` — неверный манифест либо аргументы CLI.

Вывод содержит только пути checkout’ов и краткие статусы, без diff, содержимого файлов и URL удалённых репозиториев.

Проверка ничего не клонирует, не скачивает, не переключает, не исправляет и не меняет окружение.

## Опциональный журнал текста

После проверки входных данных и согласования каркаса подготовьте полный черновик восьми секций по [workflow HVCO](../workflow.md), затем соберите чистый читательский текст.

Из корня HVCO создайте журнал для этого черновика:

```sh
python3 ../promt-copywriting/scripts/loop.py init runs/name/text-loop --source /path/to/reader-text.md --profile written
python3 ../promt-copywriting/scripts/loop.py status runs/name/text-loop
```

Подпапка `runs/name/text-loop` не должна существовать; в `runs/name/` уже могут находиться бриф и каркас, а `runs/` исключён из Git.

Профиль `written` задаёт только технические имена gates `facts`, `editorial`, `reader`; содержательные роли, порядок работы и критерии принятия задаёт HVCO.

Журнал хранит версии и отчёты, но не вызывает исполнителей и не доказывает независимость проверки.

Команды отчётов, снимков и лимитов описаны в [справке закреплённой версии журнала](https://github.com/BermanRoman/promt-copywriting/blob/bb091b6003f836106d09ed2bd5e91a8fb5d961dd/docs/loop-tool.md).
