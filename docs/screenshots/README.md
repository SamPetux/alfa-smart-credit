# Скриншоты кабинетов: что показано и как получено

Всего: 284 скриншотов, 13 готовых слайдов-композиций, 3 GIF-ролика и 2 видео. Все данные синтетические, 
интерфейс — настоящий, запущенный против настоящих API, worker и PostgreSQL. На экранах нет заранее заготовленных ответов. 
Исключения помечены: в трёх кадрах состояний («нет связи», «загрузка», «пустой список») ответ сети подменён ради снимка.

## Лучшее для презентации (`showcase/`)

| Файл | Что внутри |
|---|---|
| `01-demo-login-all-devices.png` | Вход в стенд на десктопе, планшете и телефоне |
| `02-client-home-all-devices.png` | Главная клиента на трёх устройствах |
| `03-offer-alternative-all-devices.png` | Предложение клиенту (меньшая сумма с объяснением) |
| `04-needs-info-all-devices.png` | Запрос уточнения |
| `05-bank-queue-all-devices.png` | Банковская очередь |
| `06-bank-dossier-all-devices.png` | Досье заявки |
| `07-agreement-all-devices.png` | Документ и имитация подписи |
| `10-all-client-statuses-phone.png` | Все 10 статусов заявки на телефоне |
| `11-bank-decisions-desktop.png` | Решения сотрудника: подтвердить, уточнить, отказать, перезапустить, конфликт 409 |
| `12-bank-cases-desktop.png` | Шесть разных исходов расчёта в досье |
| `13-error-and-edge-states-desktop.png` | Ошибки, загрузка, пустые состояния, 404, 409, предупреждение о потере данных |
| `14-adaptive-seven-devices-home.png` | Одна и та же главная на семи устройствах |
| `15-adaptive-seven-devices-dossier.png` | Одно и то же досье на семи устройствах |
| `flow-e01-desktop.gif`, `flow-e01-ipad.gif`, `flow-e01-iphone.gif` | Полный путь от входа до «Выдача смоделирована», 18 кадров |
| `../video/e01-desktop.webm`, `../video/e01-iphone.webm` | Тот же путь видео (около 25 секунд): клиент → сотрудник → клиент |

## Устройства

Съёмка в Chromium (Playwright) с эмуляцией экрана, плотности пикселей (×2 у планшетов и телефонов), touch и user agent. Реальных устройств, Safari и Firefox в среде нет, поэтому это эмуляция размеров и поведения касаний, а не проверка движков.

| Папка | Устройство | Экран | Набор | Обозначение в таблицах |
|---|---|---|---|---|
| `desktop-1440x900/` | Десктоп | 1440×900 | полный набор | Д |
| `laptop-1280x720/` | Ноутбук | 1280×720 | основные экраны | Н |
| `tablet-ipad-768x1024/` | iPad портрет | 768×1024, ×2 | полный набор | П |
| `tablet-ipad-landscape-1024x768/` | iPad ландшафт | 1024×768, ×2 | основные экраны | ПЛ |
| `phone-iphone-390x844/` | iPhone | 390×844, ×2 | полный набор | iPh |
| `phone-android-412x915/` | Android (Pixel) | 412×915, ×2 | основные экраны и сети | And |
| `phone-android-small-360x640/` | Небольшой Android | 360×640, ×2 | основные экраны | S |

В таблицах ниже `·` означает, что на этом устройстве кадра нет (в «основных экранах» снят не каждый).

## Данные для съёмки

Чистая база и 19 заявок двух синтетических компаний создаются `frontend/scripts/screenshots/seed.cjs` через те же API-команды, что и UI:

| Заявка | Компания | Продукт, сумма, срок | Итоговое состояние |
|---|---|---|---|
| pending_alt | ООО «Ромашка» | Оборотный, 1 000 000 ₽, 12 мес. | у специалиста, рекомендована меньшая сумма 641 000 ₽ |
| pending_full | ИП Иванов | Оборотный, 1 500 000 ₽, 18 мес. | у специалиста, рекомендована исходная сумма |
| pending_equipment | ООО «Ромашка» | Оборудование, 2 400 000 ₽, 36 мес. | у специалиста, рекомендована исходная сумма |
| pending_afford_below_min | ИП Иванов | Оборотный, 100 000 ₽, 6 мес. | у специалиста, рекомендация «Отказать» (доступная сумма ниже минимума) |
| pending_overdue | ИП Иванов | Оборотный, 600 000 ₽, 12 мес. | у специалиста, рекомендация «Отказать» (просрочка) |
| offered_full | ИП Иванов | Оборотный, 900 000 ₽, 12 мес. | предложены условия (исходная сумма) |
| offered_alt | ООО «Ромашка» | Оборотный, 1 200 000 ₽, 12 мес. | предложены условия (641 000 ₽) |
| accepted | ООО «Ромашка» | Оборотный, 500 000 ₽, 12 мес. | условия приняты, ждёт подписания |
| completed_equipment | ИП Иванов | Оборудование, 1 800 000 ₽, 24 мес. | выдача смоделирована |
| completed_large | ООО «Ромашка» | Оборотный, 3 000 000 ₽, 24 мес. | выдача смоделирована |
| declined_by_client | ИП Иванов | Оборудование, 1 200 000 ₽, 24 мес. | клиент отклонил предложение |
| rejected_overdue | ООО «Ромашка» | Оборотный, 800 000 ₽, 12 мес. | отказ сотрудника (просрочка) |
| needs_info_system | ООО «Ромашка» | Оборотный, 700 000 ₽, 12 мес. | нужны сведения: расхождение по платежам |
| needs_info_officer | ИП Иванов | Оборотный, 400 000 ₽, 6 мес. | нужны сведения по запросу сотрудника |
| resubmitted | ООО «Ромашка» | Оборотный, 650 000 ₽, 12 мес. | вторая ревизия после уточнения, у специалиста |
| error_timeout | ИП Иванов | Оборотный, 1 000 000 ₽, 12 мес. | проверка недоступна: бюро не ответило |
| error_incomplete | ООО «Ромашка» | Оборотный, 600 000 ₽, 12 мес. | проверка недоступна: неполный ответ |
| draft_empty, draft_partial | Ромашка, Иванов | Оборудование (пусто); Оборотный 450 000 ₽ | черновики |

Условия, баллы и рекомендации в этих кадрах считает серверный модуль risk-v1, в сценариях ничего не подставлено вручную. Ошибки источников включаются серверным `demo_scenario`, как в тестовой конфигурации backend.

## Клиентский кабинет (`client/`)

| Кадр | Что показывает | Д Н П ПЛ iPh And S |
|---|---|---|
| [`01-demo-login`](desktop-1440x900/client/01-demo-login.png) | Вход: карточки синтетических клиентов и сотрудника, плашка демо-режима, предупреждение о приватности | Д Н П ПЛ iPh And S |
| [`02-home-romashka`](desktop-1440x900/client/02-home-romashka.png) | Главная ООО «Ромашка»: баннер, сводка («всего» и «ждут действия»), карточки заявок с трекером этапов в разных статусах | Д Н П ПЛ iPh And S |
| [`03-home-ivanov`](desktop-1440x900/client/03-home-ivanov.png) | Главная ИП Иванов: другие заявки и данные, видны только свои (изоляция между профилями) | Д · П · iPh · · |
| [`04-new-application-choose-product`](desktop-1440x900/client/04-new-application-choose-product.png) | Новая заявка: выбор продукта, выбран «Кредит на оборудование», границы суммы, сроки и документы из API | Д Н П ПЛ iPh And S |
| [`05-draft-empty-equipment`](desktop-1440x900/client/05-draft-empty-equipment.png) | Пустой черновик кредита на оборудование: поля, подсказки по границам 300 000–5 000 000 ₽, два документа | Д · П · iPh · · |
| [`06-draft-partial`](desktop-1440x900/client/06-draft-partial.png) | Черновик ИП Иванов заполнен частично (450 000 ₽, 12 мес.), индикатор времени сохранения на сервере | Д Н П ПЛ iPh And S |
| [`07-draft-validation-errors`](desktop-1440x900/client/07-draft-validation-errors.png) | Попытка отправить неполную заявку: ошибки рядом с полями и список «Перед отправкой» | Д · П · iPh · · |
| [`08-offer-full-amount`](desktop-1440x900/client/08-offer-full-amount.png) | Предложение на исходную сумму 900 000 ₽ на 12 мес., ставка 22 %, комиссий нет; кнопки «Принять» и «Отклонить» | Д Н П ПЛ iPh And S |
| [`09-offer-alternative-amount`](desktop-1440x900/client/09-offer-alternative-amount.png) | Предложение меньшей суммы 641 000 ₽ вместо запрошенных 1 200 000 ₽ с объяснением причины | Д Н П ПЛ iPh And S |
| [`10-accepted-agreement-to-sign`](desktop-1440x900/client/10-accepted-agreement-to-sign.png) | Условия приняты: документ для ознакомления, контрольная сумма, отдельное согласие на имитацию подписи | Д Н П ПЛ iPh And S |
| [`11-completed-equipment`](desktop-1440x900/client/11-completed-equipment.png) | Выдача смоделирована: кредит на оборудование 1 800 000 ₽ на 24 мес., ставка 20 % | Д · П · iPh · · |
| [`12-completed-large-amount`](desktop-1440x900/client/12-completed-large-amount.png) | Выдача смоделирована: 3 000 000 ₽ на 24 мес. (максимум продукта) | Д · П · iPh · · |
| [`13-rejected`](desktop-1440x900/client/13-rejected.png) | Отрицательное решение сотрудника: причина (просрочка выше порога) и кнопка новой заявки | Д Н П ПЛ iPh And S |
| [`14-declined-by-client`](desktop-1440x900/client/14-declined-by-client.png) | Клиент отклонил предложение: заявка завершена | Д · П · iPh · · |
| [`15-needs-info-system-request`](desktop-1440x900/client/15-needs-info-system-request.png) | Нужны сведения: система обнаружила расхождение по платежам с бюро, клиент правит только запрошенное поле | Д Н П ПЛ iPh And S |
| [`16-needs-info-officer-request`](desktop-1440x900/client/16-needs-info-officer-request.png) | Нужны сведения: сотрудник запросил уточнение расходов с сообщением | Д · П · iPh · · |
| [`17-after-resubmit-second-revision`](desktop-1440x900/client/17-after-resubmit-second-revision.png) | После ответа на уточнение создана новая ревизия, заявка снова у специалиста | Д · П · iPh · · |
| [`18-processing-error-timeout`](desktop-1440x900/client/18-processing-error-timeout.png) | Проверка временно недоступна: бюро не ответило, это не отказ, заявка сохранена | Д Н П ПЛ iPh And S |
| [`19-processing-error-incomplete-data`](desktop-1440x900/client/19-processing-error-incomplete-data.png) | Проверка временно недоступна: неполный ответ источника (не нулевая просрочка) | Д · П · iPh · · |
| [`20-waiting-for-specialist`](desktop-1440x900/client/20-waiting-for-specialist.png) | Заявка у специалиста: проверки завершены, ожидание решения без обещаний по срокам | Д · П · iPh · · |
| [`21-home-with-application-in-progress`](desktop-1440x900/client/21-home-with-application-in-progress.png) | Главная с заявкой «Проверяем сведения» (worker на время съёмки остановлен) | Д · П · iPh · · |
| [`22-application-submitted-checking`](desktop-1440x900/client/22-application-submitted-checking.png) | Карточка заявки в проверке: трекер на этапе «Проверка», автообновление | Д · П · iPh · · |

## Банковский кабинет (`bank/`)

| Кадр | Что показывает | Д Н П ПЛ iPh And S |
|---|---|---|
| [`01-queue`](desktop-1440x900/bank/01-queue.png) | Очередь: показатели (ждут действия, всего, завершено), фильтры, статус, суммы и время без изменений | Д Н П ПЛ iPh And S |
| [`02-queue-filter-needs-action-status`](desktop-1440x900/bank/02-queue-filter-needs-action-status.png) | Очередь с серверным фильтром «Заявка у специалиста» | Д · П · iPh · · |
| [`03-queue-filter-equipment`](desktop-1440x900/bank/03-queue-filter-equipment.png) | Очередь с серверным фильтром по продукту «Кредит на оборудование» | Д · П · iPh · · |
| [`04-queue-filter-empty`](desktop-1440x900/bank/04-queue-filter-empty.png) | Пустой результат фильтра: рамка сохраняется, есть кнопка «Показать все заявки» | Д · П · iPh · · |
| [`05-dossier-alternative-amount`](desktop-1440x900/bank/05-dossier-alternative-amount.png) | Досье: рекомендация «Предложить условия» на меньшую сумму 641 000 ₽, факторы, DSCR, источники, ревизии | Д Н П ПЛ iPh And S |
| [`06-dossier-full-amount`](desktop-1440x900/bank/06-dossier-full-amount.png) | Досье: предложение на исходную сумму 1 500 000 ₽ на 18 мес. (ИП Иванов) | Д · П · iPh · · |
| [`07-dossier-equipment-product`](desktop-1440x900/bank/07-dossier-equipment-product.png) | Досье: кредит на оборудование 2 400 000 ₽ на 36 мес., ставка 20 % | Д Н П ПЛ iPh And S |
| [`08-dossier-affordability-below-minimum`](desktop-1440x900/bank/08-dossier-affordability-below-minimum.png) | Досье: доступная сумма ниже минимума продукта, рекомендация «Отказать», подтверждение условий недоступно | Д · П · iPh · · |
| [`09-dossier-overdue-reject-recommended`](desktop-1440x900/bank/09-dossier-overdue-reject-recommended.png) | Досье: просрочка выше порога, балл не рассчитан (не нулём), рекомендация «Отказать» | Д Н П ПЛ iPh And S |
| [`10-dossier-processing-error-retry`](desktop-1440x900/bank/10-dossier-processing-error-retry.png) | Досье: техническая ошибка источника, не кредитный отказ; кнопка «Перезапустить проверку» | Д Н П ПЛ iPh And S |
| [`11-dossier-source-incomplete`](desktop-1440x900/bank/11-dossier-source-incomplete.png) | Досье: источник дал неполный ответ, повторы исчерпаны | Д · П · iPh · · |
| [`12-dossier-needs-info`](desktop-1440x900/bank/12-dossier-needs-info.png) | Досье: сотрудник запросил уточнение, заявка ждёт клиента | Д · П · iPh · · |
| [`13-dossier-two-revisions`](desktop-1440x900/bank/13-dossier-two-revisions.png) | Досье: две ревизии после ответа клиента на уточнение, история изменений | Д · П · iPh · · |
| [`14-dossier-completed-history`](desktop-1440x900/bank/14-dossier-completed-history.png) | Досье завершённой заявки: полная история до «Выдача смоделирована» | Д · П · iPh · · |
| [`15-dossier-rejected`](desktop-1440x900/bank/15-dossier-rejected.png) | Досье после отказа: решение зафиксировано в истории | Д · П · iPh · · |
| [`16-dialog-approve-offer`](desktop-1440x900/bank/16-dialog-approve-offer.png) | Диалог подтверждения предложения: сотрудник видит условия, которые получит клиент | Д Н П ПЛ iPh And S |
| [`17-dialog-request-info`](desktop-1440x900/bank/17-dialog-request-info.png) | Диалог запроса уточнения: выбор полей и документов, обязательное сообщение клиенту | Д · П · iPh · · |
| [`18-dialog-reject-with-reason`](desktop-1440x900/bank/18-dialog-reject-with-reason.png) | Диалог отказа: причина из risk-v1 и обязательный комментарий | Д · П · iPh · · |
| [`19-dialog-retry-checks`](desktop-1440x900/bank/19-dialog-retry-checks.png) | Диалог перезапуска проверки после технической ошибки | Д · П · iPh · · |
| [`20-dossier-checks-not-finished`](desktop-1440x900/bank/20-dossier-checks-not-finished.png) | Досье заявки, проверки которой ещё не завершились (worker на время съёмки остановлен) | Д · П · iPh · · |

## Состояния и ошибки (`states/`)

| Кадр | Что показывает | Д Н П ПЛ iPh And S |
|---|---|---|
| [`01-foreign-application-404`](desktop-1440x900/states/01-foreign-application-404.png) | Открыть чужую заявку по ссылке: сервер отвечает 404, данные не раскрываются | Д Н П ПЛ iPh And S |
| [`02-wrong-role-screen`](desktop-1440x900/states/02-wrong-role-screen.png) | Сотрудник открывает клиентский раздел: объяснение и ссылка в свой кабинет | Д · П · iPh · · |
| [`03-page-not-found`](desktop-1440x900/states/03-page-not-found.png) | Несуществующий адрес | Д · П · iPh · · |
| [`04-client-profile-open-on-demo`](desktop-1440x900/states/04-client-profile-open-on-demo.png) | Вход при уже открытом профиле: «Продолжить в этом профиле» или сменить | Д · П · iPh · · |
| [`05-network-error-with-retry`](desktop-1440x900/states/05-network-error-with-retry.png) | Нет связи с сервером: ошибка внутри блока с кнопкой «Повторить» (сеть подменена для снимка) | Д · П · iPh And · |
| [`06-loading-skeleton`](desktop-1440x900/states/06-loading-skeleton.png) | Загрузка: серые плашки в размер содержимого, без блеска (ответ сервера задержан для снимка) | Д · П · iPh And · |
| [`07-empty-applications-list`](desktop-1440x900/states/07-empty-applications-list.png) | Пустой список заявок с призывом создать первую (ответ API подменён для снимка) | Д · П · iPh And · |
| [`08-draft-version-conflict-409`](desktop-1440x900/states/08-draft-version-conflict-409.png) | Конфликт версий черновика (409): правки не потеряны молча, есть «Загрузить актуальную версию» | Д · П · iPh · · |
| [`09-unsaved-changes-warning`](desktop-1440x900/states/09-unsaved-changes-warning.png) | Предупреждение при уходе с несохранёнными правками | Д · П · iPh · · |
| [`10-bank-decision-conflict-409`](desktop-1440x900/states/10-bank-decision-conflict-409.png) | Решение сотрудника при устаревших данных: 409, действие не применено, досье обновлено | Д · П · iPh · · |
| [`11-keyboard-focus-visible`](desktop-1440x900/states/11-keyboard-focus-visible.png) | Видимый фокус при навигации с клавиатуры | Д · П · iPh · · |

## Полный путь от входа до выдачи (`flow/`)

Путь проходит через UI: клиент оформляет заявку, переключает профиль на сотрудника, подтверждает предложение, возвращается к клиенту, принимает условия и подписывает.

- **Десктоп** (`desktop-1440x900/flow/`): ООО «Ромашка», оборотный кредит 1 000 000 ₽ на 12 мес. (выручка 600 000, расходы 400 000, долги 100 000): меньшая сумма 641 000 ₽
- **iPad портрет** (`tablet-ipad-768x1024/flow/`): ИП Иванов, оборотный кредит 1 500 000 ₽ на 18 мес.: предложение на исходную сумму
- **iPhone** (`phone-iphone-390x844/flow/`): ООО «Ромашка», кредит на оборудование 2 400 000 ₽ на 36 мес. с двумя документами

| Кадр | Что показывает | Д Н П ПЛ iPh And S |
|---|---|---|
| [`01-demo-choose-profile`](desktop-1440x900/flow/01-demo-choose-profile.png) | Выбор профиля клиента | Д · П · iPh · · |
| [`02-choose-product`](desktop-1440x900/flow/02-choose-product.png) | Выбор продукта | Д · П · iPh · · |
| [`03-empty-draft`](desktop-1440x900/flow/03-empty-draft.png) | Пустой черновик | Д · П · iPh · · |
| [`04-validation-errors`](desktop-1440x900/flow/04-validation-errors.png) | Ошибки при попытке отправить пустую форму | Д · П · iPh · · |
| [`05-filled-unsaved-changes`](desktop-1440x900/flow/05-filled-unsaved-changes.png) | Форма заполнена, есть несохранённые изменения | Д · П · iPh · · |
| [`06-saved-and-documents-uploaded`](desktop-1440x900/flow/06-saved-and-documents-uploaded.png) | Черновик сохранён на сервере, документы загружены | Д · П · iPh · · |
| [`07-confirm-submit-dialog`](desktop-1440x900/flow/07-confirm-submit-dialog.png) | Подтверждение отправки | Д · П · iPh · · |
| [`08-submitted-toast-and-stepper`](desktop-1440x900/flow/08-submitted-toast-and-stepper.png) | Заявка отправлена: уведомление, трекер, статус «Проверяем сведения» | Д · П · iPh · · |
| [`09-waiting-for-specialist`](desktop-1440x900/flow/09-waiting-for-specialist.png) | Проверки завершены, заявка у специалиста | Д · П · iPh · · |
| [`10-officer-queue-new-application`](desktop-1440x900/flow/10-officer-queue-new-application.png) | Смена профиля на сотрудника: очередь с новой заявкой | Д · П · iPh · · |
| [`11-officer-dossier`](desktop-1440x900/flow/11-officer-dossier.png) | Досье с рекомендацией | Д · П · iPh · · |
| [`12-officer-approve-dialog`](desktop-1440x900/flow/12-officer-approve-dialog.png) | Подтверждение предложения | Д · П · iPh · · |
| [`13-officer-approved-toast`](desktop-1440x900/flow/13-officer-approved-toast.png) | Предложение подтверждено: уведомление и обновлённый статус | Д · П · iPh · · |
| [`14-client-home-new-card`](desktop-1440x900/flow/14-client-home-new-card.png) | Смена профиля обратно на клиента: главная | Д · П · iPh · · |
| [`15-client-offer`](desktop-1440x900/flow/15-client-offer.png) | Предложение клиенту | Д · П · iPh · · |
| [`16-accepted-toast-and-agreement`](desktop-1440x900/flow/16-accepted-toast-and-agreement.png) | Условия приняты: уведомление и документ для ознакомления | Д · П · iPh · · |
| [`17-consent-checked`](desktop-1440x900/flow/17-consent-checked.png) | Отмечено согласие на имитацию подписи | Д · П · iPh · · |
| [`18-completed-simulation`](desktop-1440x900/flow/18-completed-simulation.png) | «Выдача смоделирована. Реальные средства не переводились» | Д · П · iPh · · |

## Как воспроизвести

```bash
# 1. Поднять стенд (Postgres, API, worker) и собрать frontend: см. frontend/README.md
# 2. Из каталога frontend/scripts/screenshots (нужен Playwright):
node seed.cjs                          # чистая база → 19 заявок
node capture.cjs views desktop iphone  # статичные экраны выбранных устройств (или all)
node capture.cjs final desktop ipad iphone  # пути, конфликты, «в обработке»
python3 showcase.py                    # композиции и GIF
python3 gen_readme.py                  # этот файл
```

Устройства описаны в `devices.cjs`. Скрипты работают только против локального стенда с синтетическими данными.
