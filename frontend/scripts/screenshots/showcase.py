"""Собирает витрину из готовых скриншотов: композиции по устройствам, сетки статусов, GIF-ролики путей.

Запуск: python3 showcase.py [каталог docs/screenshots]. Исходные снимки не меняются.
Подписи на композициях рисуются шрифтом DejaVu Sans (системный, с кириллицей).
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[3] / "docs" / "screenshots")
OUT = ROOT / "showcase"
OUT.mkdir(parents=True, exist_ok=True)

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BG_TOP, BG_BOTTOM = (242, 243, 245), (228, 230, 235)
INK, MUTED, RED = (33, 33, 36), (107, 107, 117), (227, 42, 23)

DESKTOP, TABLET, PHONE = "desktop-1440x900", "tablet-ipad-768x1024", "phone-iphone-390x844"
STATUS_TITLES = {
    "client/06-draft-partial": "Черновик",
    "client/22-application-submitted-checking": "Проверяем сведения",
    "client/15-needs-info-system-request": "Нужны сведения",
    "client/18-processing-error-timeout": "Проверка недоступна",
    "client/20-waiting-for-specialist": "У специалиста",
    "client/08-offer-full-amount": "Предложены условия",
    "client/10-accepted-agreement-to-sign": "Условия приняты",
    "client/11-completed-equipment": "Выдача смоделирована",
    "client/13-rejected": "Отрицательное решение",
    "client/14-declined-by-client": "Отклонено клиентом",
}


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def gradient(size):
    w, h = size
    img = Image.new("RGB", size, BG_TOP)
    px = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        px.line([(0, y), (w, y)], fill=tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3)))
    return img


def load(rel):
    path = ROOT / f"{rel}.png"
    return Image.open(path).convert("RGB") if path.exists() else None


def top_crop(img, aspect_h_over_w, width_px, skip=0.0):
    """Часть страницы нужного соотношения (с отступом сверху skip×ширины), масштабированная до ширины."""
    w, h = img.size
    y0 = min(int(w * skip), max(h - 1, 0))
    crop_h = min(h - y0, int(w * aspect_h_over_w))
    out = img.crop((0, y0, w, y0 + crop_h))
    scale = width_px / w
    return out.resize((width_px, max(1, int(crop_h * scale))), Image.LANCZOS)


def rounded(img, radius):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *img.size), radius, fill=255)
    out = Image.new("RGBA", img.size)
    out.paste(img, (0, 0), mask)
    return out


def shadow(canvas, box, radius, blur=28, offset=(0, 18), opacity=70):
    from PIL import ImageFilter

    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    x0, y0, x1, y1 = box
    ImageDraw.Draw(layer).rounded_rectangle((x0 + offset[0], y0 + offset[1], x1 + offset[0], y1 + offset[1]), radius, fill=(10, 10, 20, opacity))
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur)))


def browser_frame(canvas, shot, x, y, width):
    body = top_crop(shot, 0.625, width)
    bar_h = 34
    box = (x, y, x + width, y + bar_h + body.height)
    shadow(canvas, box, 18)
    frame = Image.new("RGBA", (width, bar_h + body.height), (255, 255, 255, 255))
    d = ImageDraw.Draw(frame)
    d.rectangle((0, 0, width, bar_h), fill=(236, 237, 240))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((16 + i * 22, 11, 28 + i * 22, 23), fill=c)
    d.rounded_rectangle((width * 0.28, 7, width * 0.72, 27), 10, fill=(255, 255, 255))
    frame.paste(body, (0, bar_h))
    canvas.alpha_composite(rounded(frame.convert("RGB"), 18), (x, y))
    return box


def device_frame(canvas, shot, x, y, width, aspect, radius, bezel, notch=False, skip=0.0):
    inner = top_crop(shot, aspect, width, skip)
    w, h = inner.width + bezel * 2, inner.height + bezel * 2
    box = (x, y, x + w, y + h)
    shadow(canvas, box, radius + bezel)
    frame = Image.new("RGBA", (w, h), (24, 24, 28, 255))
    mask_inner = rounded(inner, max(radius - 4, 6))
    frame.alpha_composite(mask_inner, (bezel, bezel))
    d = ImageDraw.Draw(frame)
    if notch:
        d.rounded_rectangle((w / 2 - 26, 4, w / 2 + 26, 9), 3, fill=(60, 60, 66))
    canvas.alpha_composite(rounded(frame.convert("RGB"), radius + bezel), (x, y))
    return box


def caption(canvas, text, xy, size=18, fill=MUTED, bold=False, anchor="la"):
    ImageDraw.Draw(canvas).text(xy, text, font=font(size, bold), fill=fill, anchor=anchor)


def multi_device(name, rel, title, subtitle):
    d, t, p = load(f"{DESKTOP}/{rel}"), load(f"{TABLET}/{rel}"), load(f"{PHONE}/{rel}")
    if not (d and t and p):
        print("skip", name, "missing", rel)
        return
    canvas = gradient((2400, 1350)).convert("RGBA")
    caption(canvas, title, (110, 90), 44, INK, True)
    caption(canvas, subtitle, (110, 152), 24, MUTED)
    ImageDraw.Draw(canvas).rounded_rectangle((110, 62, 150, 70), 4, fill=RED)
    bx = browser_frame(canvas, d, 110, 250, 1330)
    caption(canvas, "Десктоп 1440×900", (110 + 665, bx[3] + 22), 20, MUTED, anchor="ma")
    tb = device_frame(canvas, t, 1500, 330, 420, 1.2, 38, 14)
    caption(canvas, "Планшет iPad 768×1024", ((tb[0] + tb[2]) // 2, tb[3] + 22), 20, MUTED, anchor="ma")
    pb = device_frame(canvas, p, 1990, 430, 270, 1.6, 40, 11, notch=True)
    caption(canvas, "Телефон iPhone 390×844", ((pb[0] + pb[2]) // 2, pb[3] + 22), 20, MUTED, anchor="ma")
    canvas.convert("RGB").save(OUT / f"{name}.png", optimize=True)
    print("showcase", name)


def phone_grid(name, items, title, subtitle, columns=5, device=PHONE, aspect=1.7, width=300):
    shots = [(label, load(f"{device}/{rel}")) for rel, label in items]
    shots = [(label, img) for label, img in shots if img]
    if not shots:
        return
    rows = (len(shots) + columns - 1) // columns
    gap, pad = 36, 90
    height = top_crop(shots[0][1], aspect, width - 24, 0.5).height + 24
    cw = pad * 2 + columns * width + (columns - 1) * gap
    ch = 230 + rows * (height + 100) + pad
    canvas = gradient((cw, ch)).convert("RGBA")
    caption(canvas, title, (pad, 80), 44, INK, True)
    caption(canvas, subtitle, (pad, 142), 24, MUTED)
    ImageDraw.Draw(canvas).rounded_rectangle((pad, 54, pad + 40, 62), 4, fill=RED)
    for i, (label, img) in enumerate(shots):
        r, c = divmod(i, columns)
        x, y = pad + c * (width + gap), 230 + r * (height + 100)
        device_frame(canvas, img, x, y, width - 24, aspect, 34, 12, notch=True, skip=0.5)
        caption(canvas, label, (x + width // 2, y + height + 28), 21, INK, True, "ma")
    canvas.convert("RGB").save(OUT / f"{name}.png", optimize=True)
    print("showcase", name)


def desktop_grid(name, items, title, subtitle, columns=3, width=720):
    shots = [(label, load(f"{DESKTOP}/{rel}")) for rel, label in items]
    shots = [(label, img) for label, img in shots if img]
    if not shots:
        return
    rows = (len(shots) + columns - 1) // columns
    gap, pad = 40, 90
    body_h = top_crop(shots[0][1], 0.625, width).height + 34
    cw = pad * 2 + columns * width + (columns - 1) * gap
    ch = 230 + rows * (body_h + 110) + pad
    canvas = gradient((cw, ch)).convert("RGBA")
    caption(canvas, title, (pad, 80), 44, INK, True)
    caption(canvas, subtitle, (pad, 142), 24, MUTED)
    ImageDraw.Draw(canvas).rounded_rectangle((pad, 54, pad + 40, 62), 4, fill=RED)
    for i, (label, img) in enumerate(shots):
        r, c = divmod(i, columns)
        x, y = pad + c * (width + gap), 230 + r * (body_h + 110)
        browser_frame(canvas, img, x, y, width)
        caption(canvas, label, (x + width // 2, y + body_h + 26), 21, INK, True, "ma")
    canvas.convert("RGB").save(OUT / f"{name}.png", optimize=True)
    print("showcase", name)


def device_row(name, rel, title, subtitle):
    devices = [
        ("desktop-1440x900", "Десктоп 1440", 0.625, 520, "browser"),
        ("laptop-1280x720", "Ноутбук 1280", 0.5625, 440, "browser"),
        ("tablet-ipad-landscape-1024x768", "iPad ландшафт 1024", 0.75, 380, "tablet"),
        ("tablet-ipad-768x1024", "iPad портрет 768", 1.3, 250, "tablet"),
        ("phone-android-412x915", "Android 412", 1.9, 200, "phone"),
        ("phone-iphone-390x844", "iPhone 390", 1.9, 200, "phone"),
        ("phone-android-small-360x640", "Android 360", 1.75, 190, "phone"),
    ]
    imgs = [(label, load(f"{d}/{rel}"), a, w, kind) for d, label, a, w, kind in devices]
    imgs = [i for i in imgs if i[1]]
    pad, gap = 80, 40
    total_w = pad * 2 + sum(w + 28 for _, _, _, w, _ in imgs) + gap * (len(imgs) - 1)
    canvas = gradient((total_w, 800)).convert("RGBA")
    caption(canvas, title, (pad, 70), 44, INK, True)
    caption(canvas, subtitle, (pad, 132), 24, MUTED)
    ImageDraw.Draw(canvas).rounded_rectangle((pad, 44, pad + 40, 52), 4, fill=RED)
    x = pad
    base = 700
    for label, img, aspect, w, kind in imgs:
        if kind == "browser":
            body = top_crop(img, aspect, w)
            y = base - body.height - 34
            box = browser_frame(canvas, img, x, y, w)
            cx = x + w // 2
            x += w + gap
        else:
            inner = top_crop(img, aspect, w)
            h = inner.height + 28
            box = device_frame(canvas, img, x, base - h, w, aspect, 30 if kind == "tablet" else 36, 14 if kind == "tablet" else 11, notch=kind == "phone")
            cx = x + (w + 28) // 2
            x += w + 28 + gap
        caption(canvas, label, (cx, base + 24), 19, MUTED, anchor="ma")
    canvas.convert("RGB").save(OUT / f"{name}.png", optimize=True)
    print("showcase", name)


def gif(name, device, duration=1400, width=None):
    frames_dir = ROOT / device / "flow"
    files = sorted(frames_dir.glob("*.png"))
    if not files:
        return
    frames = []
    for f in files:
        img = Image.open(f).convert("RGB")
        # Кадр — верхняя часть экрана, чтобы GIF оставался лёгким и читаемым.
        w, h = img.size
        img = img.crop((0, 0, w, min(h, int(w * (1.7 if w < 800 else 0.625)))))
        target_w = width or (420 if w < 800 else 1000)
        img = img.resize((target_w, int(img.height * target_w / w)), Image.LANCZOS)
        frames.append(img.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
    frames[0].save(OUT / f"{name}.gif", save_all=True, append_images=frames[1:], duration=duration, loop=0, optimize=True)
    print("gif", name, len(frames), "frames")


def main():
    multi_device("01-demo-login-all-devices", "client/01-demo-login", "Вход в демонстрационный стенд", "Профили клиентов и сотрудника, явная пометка демо-режима")
    multi_device("02-client-home-all-devices", "client/02-home-romashka", "Кабинет клиента: заявки компании", "Карточки со статусом, суммой и трекером этапов")
    multi_device("03-offer-alternative-all-devices", "client/09-offer-alternative-amount", "Предложение клиенту", "Условия считает сервер; причина меньшей суммы объяснена")
    multi_device("04-needs-info-all-devices", "client/15-needs-info-system-request", "Запрос уточнения", "Клиент исправляет только запрошенные сведения и отправляет новую ревизию")
    multi_device("05-bank-queue-all-devices", "bank/01-queue", "Банк: очередь заявок", "Фильтры на сервере, показатели очереди, статус и необходимость действия")
    multi_device("06-bank-dossier-all-devices", "bank/05-dossier-alternative-amount", "Банк: досье заявки", "Рекомендация, факторы, доступность, источники, ревизии и история")
    multi_device("07-agreement-all-devices", "client/10-accepted-agreement-to-sign", "Документ и имитация подписи", "Отдельное согласие клиента; явная метка «имитация»")

    phone_grid(
        "10-all-client-statuses-phone",
        [(rel, label) for rel, label in STATUS_TITLES.items()],
        "Все статусы заявки глазами клиента",
        "Подписи берутся из contracts/statuses.json. Телефон iPhone 390×844",
        columns=5,
    )
    desktop_grid(
        "11-bank-decisions-desktop",
        [
            ("bank/16-dialog-approve-offer", "Подтвердить предложение"),
            ("bank/17-dialog-request-info", "Запросить уточнение"),
            ("bank/18-dialog-reject-with-reason", "Отказать с причиной"),
            ("bank/19-dialog-retry-checks", "Перезапустить проверку"),
            ("states/10-bank-decision-conflict-409", "Конфликт версий (409)"),
            ("bank/09-dossier-overdue-reject-recommended", "Отрицательная рекомендация"),
        ],
        "Банк: решения сотрудника",
        "Каждое действие подтверждается; устаревшие данные не применяются",
    )
    desktop_grid(
        "12-bank-cases-desktop",
        [
            ("bank/05-dossier-alternative-amount", "Меньшая сумма по DSCR"),
            ("bank/06-dossier-full-amount", "Исходная сумма"),
            ("bank/07-dossier-equipment-product", "Кредит на оборудование"),
            ("bank/08-dossier-affordability-below-minimum", "Сумма ниже минимума продукта"),
            ("bank/10-dossier-processing-error-retry", "Сбой источника: повтор"),
            ("bank/13-dossier-two-revisions", "Две ревизии после уточнения"),
        ],
        "Банк: разные кейсы",
        "Разные суммы, продукты и исходы расчёта на синтетических данных",
    )
    desktop_grid(
        "13-error-and-edge-states-desktop",
        [
            ("states/01-foreign-application-404", "Чужая заявка: 404"),
            ("states/02-wrong-role-screen", "Не та роль"),
            ("states/05-network-error-with-retry", "Нет связи: повтор"),
            ("states/06-loading-skeleton", "Загрузка"),
            ("states/07-empty-applications-list", "Пустой список"),
            ("client/07-draft-validation-errors", "Ошибки в полях"),
            ("states/08-draft-version-conflict-409", "Конфликт версий (409)"),
            ("states/09-unsaved-changes-warning", "Несохранённые правки"),
            ("states/11-keyboard-focus-visible", "Фокус с клавиатуры"),
        ],
        "Состояния и ошибки",
        "Loading, empty, error, 404, 409 и предупреждение о потере данных",
    )
    device_row("14-adaptive-seven-devices-home", "client/02-home-romashka", "Один интерфейс на семи устройствах", "Главная клиента: десктоп, ноутбук, iPad (портрет и ландшафт), iPhone и два Android")
    device_row("15-adaptive-seven-devices-dossier", "bank/05-dossier-alternative-amount", "Досье сотрудника на семи устройствах", "Тот же экран, адаптированный под размер")
    gif("flow-e01-desktop", DESKTOP)
    gif("flow-e01-iphone", PHONE, duration=1300)
    gif("flow-e01-ipad", TABLET, duration=1300, width=500)


if __name__ == "__main__":
    main()
