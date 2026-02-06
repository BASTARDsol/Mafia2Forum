# Mafia2RP: план внедрения семейного CRM-блока (Операции + Кадры)

Документ описывает **двухэтапное внедрение** с фокусом на быстрый эффект:
1) «Операции» (подготовка/проведение/разбор),
2) «Кадровый контур» (вербовка/испытательный срок/повышения).

---

## Цели этапов

- Ускорить координацию RP-активностей внутри семьи.
- Сделать ответственность прозрачной (кто назначил, кто выполнил, кто согласовал).
- Встроить процессный контур в текущую форумную механику (темы, статусы, уведомления).

---

## Этап 1 (MVP, 1–2 недели): «Операции» + базовый «Кадры»

### 1) Модели (Django)

#### Операции
- `Operation`
  - `title` (CharField)
  - `goal` (TextField)
  - `coordinator` (FK -> User)
  - `planned_start_at` (DateTimeField)
  - `planned_end_at` (DateTimeField, null=True)
  - `status` (choices: draft / planned / active / completed / failed / archived)
  - `result_summary` (TextField, blank=True)
  - `created_by` (FK -> User)
  - `created_at`, `updated_at`

- `OperationMember`
  - `operation` (FK -> Operation)
  - `user` (FK -> User)
  - `role_in_operation` (CharField, например driver / shooter / scout / negotiator)
  - `is_confirmed` (BooleanField)
  - `joined_at`

- `OperationChecklistItem`
  - `operation` (FK -> Operation)
  - `kind` (choices: weapons / transport / comms / intel / finance)
  - `title`
  - `is_done` (BooleanField)
  - `done_by` (FK -> User, null=True)
  - `done_at` (DateTimeField, null=True)

- `OperationDebrief`
  - `operation` (OneToOne -> Operation)
  - `report_text` (TextField)
  - `lessons_learned` (TextField)
  - `losses` (TextField, blank=True)
  - `approved_by` (FK -> User, null=True)
  - `approved_at` (DateTimeField, null=True)

#### Кадры (база)
- `RecruitmentApplication`
  - `nickname` (CharField)
  - `source` (CharField: откуда кандидат)
  - `motivation` (TextField)
  - `stage` (choices: new / interview / check / trial / accepted / rejected)
  - `curator` (FK -> User, null=True)
  - `trial_ends_at` (DateField, null=True)
  - `decision_comment` (TextField, blank=True)
  - `created_by` (FK -> User)
  - `created_at`, `updated_at`

- `RankHistory`
  - `user` (FK -> User)
  - `old_rank` (CharField)
  - `new_rank` (CharField)
  - `reason` (TextField)
  - `changed_by` (FK -> User)
  - `changed_at`

> Для этапа 1 ранги можно хранить как enum в профиле (`associate/soldato/capo/consigliere/don`) без сложной орг-структуры.

---

### 2) URL-структура

```text
/family/operations/
/family/operations/create/
/family/operations/<id>/
/family/operations/<id>/edit/
/family/operations/<id>/checklist/
/family/operations/<id>/debrief/

/family/hr/recruitment/
/family/hr/recruitment/create/
/family/hr/recruitment/<id>/
/family/hr/recruitment/<id>/stage/
/family/hr/ranks/
```

---

### 3) Шаблоны

- `main/templates/main/family/operations_list.html`
- `main/templates/main/family/operation_form.html`
- `main/templates/main/family/operation_detail.html`
- `main/templates/main/family/operation_debrief_form.html`
- `main/templates/main/family/recruitment_list.html`
- `main/templates/main/family/recruitment_detail.html`

#### Что важно в UI MVP
- Бейджи статуса операции (planned/active/completed/failed).
- Чек-лист с быстрым переключением «выполнено/не выполнено».
- Блок «уроки операции» внизу карточки.
- Для кадров: канбан-представление этапов кандидата (или минимум фильтры по `stage`).

---

### 4) Права доступа

#### Ролевая матрица (минимальная)
- **soldato**: просмотр назначенных операций, комментарии в отчёте.
- **capo**: создание операций, управление составом и чек-листом.
- **consigliere**: доступ к кадровым решениям, согласование отчётов.
- **don**: финальное утверждение debrief, изменение критичных статусов, read-only lock протокола.

#### Реализация прав (MVP)
- Django Groups: `family_soldato`, `family_capo`, `family_consigliere`, `family_don`.
- Декораторы/миксины на view:
  - `CanViewOperation`, `CanManageOperation`, `CanApproveDebrief`, `CanManageRecruitment`.

---

### 5) Интеграция с существующим форумом

- Операция может ссылаться на тему (`Topic`) как на «ветку обсуждения/доказательств».
- Финальный debrief автоматически постится в связанную тему (опционально).
- Использовать существующие уведомления для пингов:
  - назначен в операцию,
  - changed stage кандидата,
  - операция переведена в `active/completed`.

---

### 6) Критерии готовности этапа 1

- Можно создать операцию, назначить состав, закрыть чек-лист, оформить debrief.
- Можно провести кандидата по этапам до `accepted/rejected`.
- Есть базовые ролевые ограничения на действия.
- Все изменения фиксируются в истории (кто/когда/что поменял).

---

## Этап 2 (расширение, 2–4 недели): аналитика + досье + дисциплина

### 1) Расширенные модели

- `DossierEntry` (человек/фракция, статус: ally/neutral/enemy, threat_level, last_incident)
- `DossierChangeLog` (кто и почему изменил статус)
- `DisciplinaryCase` (warning/fine/suspension + доказательства)
- `FamilyTask` (поручения от капо, дедлайн, статус)
- `TerritoryInfluence` (район, контроль, риск, прибыль)

---

### 2) URL-структура этапа 2

```text
/family/dossiers/
/family/dossiers/<id>/
/family/discipline/
/family/tasks/
/family/territories/
/family/reports/weekly/
```

---

### 3) Шаблоны и UX-фичи этапа 2

- Шапка «Оперативная обстановка» (flash-апдейты).
- Иконки префиксов тем: Важно / Операция / Досье / Финансы / Кадры.
- RP-таймлайн дня.
- «Ночной штаб» (усиленный тёмный контраст).

---

### 4) Права и аудит этапа 2

- Раздельный доступ к финансовому блоку (казначей/consigliere/don).
- Лог чтения чувствительных разделов (кто открывал карточки досье/дисциплины).
- Политика неизменяемости утверждённых протоколов (write lock).

---

## Технический план внедрения

1. Создать модели и миграции для этапа 1.
2. Добавить admin-панели с фильтрами и поиском.
3. Поднять базовые CRUD-views и шаблоны.
4. Подключить ролевой доступ (Groups + permission mixins).
5. Привязать уведомления к ключевым событиям.
6. Добавить журнал изменений (audit trail) для операций и кадров.
7. Нагрузочно проверить списки/фильтры на больших объёмах данных.

---

## Риски и как снизить

- **Сложность прав**: сначала жёсткая матрица, затем тонкие ACL.
- **Конфликты по данным**: обязательный audit log + неизменяемые финальные статусы.
- **Переусложнение MVP**: этап 1 держать узким, без «территорий/финансов».
- **Низкая адаптация игроков**: короткие шаблоны, автоподстановка полей и минимальный ввод вручную.

---

## Что внедрять первым (порядок)

1. Операции + debrief + чек-лист.
2. Вербовка + этапы + испытательный срок.
3. История рангов.
4. Досье и дисциплина.

Это даст самый заметный эффект: ощущение «живого штаба семьи» без перегруза интерфейса.
