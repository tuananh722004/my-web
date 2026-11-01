#!/usr/bin/env python3
"""
💖 TỎ TÌNH BẰNG PYTHON 💖
-------------------------------------------------
Chỉ dùng thư viện có sẵn của Python (tkinter) - KHÔNG cần cài thêm gì.

Chức năng:
  * Trái tim đập thịch-thịch, phát sáng, có lớp bóng 3D
  * Bầu trời sao lấp lánh + tim bay lên liên tục
  * Lời tỏ tình tự "gõ chữ" từng dòng
  * Câu hỏi cuối cùng với 2 nút:
      - "Đồng ý" càng lúc càng to
      - "Không" chạy trốn con trỏ chuột, đổi chữ trêu chọc
  * Bấm "Đồng ý" -> pháo hoa + mưa tim + lời yêu thương
  * Click chuột bất kỳ đâu -> tim bắn tung toé
  * Nhấn ESC để thoát

Cách chạy:
    python to_tinh.py
    python to_tinh.py "Linh" "Nam"      # tên người ấy, tên bạn

Hãy sửa phần CẤU HÌNH bên dưới cho đúng với bạn nhé!
"""
import math
import random
import sys
import time
import tkinter as tk

# ====================== CẤU HÌNH (SỬA Ở ĐÂY) ======================
TEN_NGUOI_AY = "Việt Anh"   # người nhận, người được tỏ tình
TEN_BAN = "Lâm"             # người gửi, tức là bạn

LOI_NHAN = [               # các dòng sẽ được gõ chữ lần lượt
    "Xin chào {ten}...",
    "Có một điều anh giấu trong lòng từ lâu rồi.",
    "Từ ngày có em, mọi thứ xung quanh đều đẹp hơn.",
    "Mỗi lần thấy em cười, tim anh lại đập nhanh hơn.",
    "Hôm nay anh muốn nói thật lòng...",
]
CAU_HOI = "{ten} ơi, làm người yêu anh nhé?"

LOI_DONG_Y = [             # hiện ra khi bấm "Đồng ý"
    "Anh yêu em, {ten}!",
    "Cảm ơn em đã đến bên anh.",
]
NHAN_NUT_KHONG = [         # chữ trên nút "Không" mỗi lần nó chạy trốn
    "Không", "Chắc chưa?", "Nghĩ lại đi mà", "Đừng mà...",
    "Bấm Đồng ý đi", "Hết đường chạy rồi", "Thôi đồng ý đi!",
]
# ==================================================================

W, H = 800, 680
BG = "#0b0614"
PALETTE = ["#ff2e63", "#ff6b8b", "#ff9db1", "#ffd1dc", "#ff5e78", "#ffb3c6", "#ffffff"]


# ----------------------------- tiện ích ---------------------------
def _rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def mix(c1, c2, a):
    """Pha màu c1 -> c2 theo tỉ lệ a (0..1). Dùng để giả lập độ trong suốt."""
    a = max(0.0, min(1.0, a))
    r1, g1, b1 = _rgb(c1)
    r2, g2, b2 = _rgb(c2)
    return "#%02x%02x%02x" % (int(r1 + (r2 - r1) * a),
                              int(g1 + (g2 - g1) * a),
                              int(b1 + (b2 - b1) * a))


# Đường cong trái tim (đã dời về tâm)
_N = 90
BASE = []
for _i in range(_N):
    _t = 2 * math.pi * _i / _N
    BASE.append((16 * math.sin(_t) ** 3,
                 13 * math.cos(_t) - 5 * math.cos(2 * _t)
                 - 2 * math.cos(3 * _t) - math.cos(4 * _t) + 2.5))


BASE_SMALL = BASE[::3]   # ít điểm hơn cho các tim nhỏ -> nhẹ máy


def heart_poly(cx, cy, s, k=1.0, dx=0.0, dy=0.0, small=False):
    pts = []
    for x, y in (BASE_SMALL if small else BASE):
        pts.append(cx + (x * k + dx) * s)
        pts.append(cy - (y * k + dy) * s)
    return pts


# ------------------------------ ứng dụng --------------------------
class LoveApp:
    def __init__(self, root, ten, ban):
        self.root = root
        self.ten, self.ban = ten, ban
        root.title("Gửi " + ten)  
        root.resizable(False, False)
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry("%dx%d+%d+%d" % (W, H, (sw - W) // 2, max(0, (sh - H) // 3)))
        self.c = tk.Canvas(root, width=W, height=H, bg=BG, highlightthickness=0)
        self.c.pack()

        self.lines = [s.format(ten=ten) for s in LOI_NHAN]
        self.question = CAU_HOI.format(ten=ten)
        self.final = [s.format(ten=ten) for s in LOI_DONG_Y]

        self.stars = [(random.uniform(0, W), random.uniform(0, H),
                       random.uniform(0.8, 2.2), random.uniform(0, 6.28))
                      for _ in range(90)]
        self.hearts = []     # tim bay lên
        self.sparks = []     # pháo hoa / tim bắn
        self.spawn_acc = 0.0
        self.next_fw = 0.0

        self.stage = "intro"   # intro -> ask -> yes
        self.li, self.ci, self.hold_until = 0, 0.0, None
        self.qi = 0.0

        self.yes_scale = 1.0
        self.dodges = 0
        self.yes_c = [W / 2 - 120, 590]
        self.no_c = [W / 2 + 120, 590]
        self.no_label = NHAN_NUT_KHONG[0]
        self.mx = self.my = -999

        self.t0 = self.last = time.time()
        self.t = 0.0

        root.bind("<Escape>", lambda e: root.destroy())
        self.c.bind("<Motion>", self.on_motion)
        self.c.bind("<Button-1>", self.on_click)
        self.tick()

    # ------------------------- sự kiện chuột ------------------------
    def yes_box(self):
        w, h = 150 * self.yes_scale, 54 * self.yes_scale
        x, y = self.yes_c
        return x - w / 2, y - h / 2, x + w / 2, y + h / 2

    def no_box(self):
        x, y = self.no_c
        return x - 85, y - 25, x + 85, y + 25

    @staticmethod
    def inside(box, x, y, pad=0):
        return box[0] - pad <= x <= box[2] + pad and box[1] - pad <= y <= box[3] + pad

    def on_motion(self, e):
        self.mx, self.my = e.x, e.y
        if self.stage == "ask" and self.inside(self.no_box(), e.x, e.y, 35):
            self.dodge(e.x, e.y)

    def on_click(self, e):
        if self.stage == "ask":
            if self.inside(self.yes_box(), e.x, e.y):
                return self.say_yes()
            if self.inside(self.no_box(), e.x, e.y):
                return self.dodge(e.x, e.y)
        self.pop(e.x, e.y)

    def dodge(self, mx, my):
        self.dodges += 1
        self.no_label = NHAN_NUT_KHONG[min(self.dodges, len(NHAN_NUT_KHONG) - 1)]
        self.yes_scale = min(1.9, 1 + 0.1 * self.dodges)
        yb = self.yes_box()
        for _ in range(80):
            x, y = random.uniform(100, W - 100), random.uniform(530, H - 40)
            if math.hypot(x - mx, y - my) < 190:
                continue
            if yb[0] - 70 < x < yb[2] + 70 and yb[1] - 45 < y < yb[3] + 45:
                continue
            self.no_c = [x, y]
            break

    def say_yes(self):
        self.stage = "yes"
        self.yes_t = self.t
        for _ in range(5):
            self.firework(random.uniform(120, W - 120), random.uniform(90, 330))

    # --------------------------- hiệu ứng ---------------------------
    def spawn_heart(self):
        self.hearts.append(dict(
            x0=random.uniform(0, W), y=H + 30, s=random.uniform(0.35, 1.2),
            v=random.uniform(40, 120), amp=random.uniform(10, 40),
            ph=random.uniform(0, 6.28), f=random.uniform(0.8, 2.0),
            col=random.choice(PALETTE)))

    def pop(self, x, y):
        for _ in range(12):
            a = random.uniform(0, 6.28)
            sp = random.uniform(60, 220)
            self.sparks.append(dict(
                x=x, y=y, vx=math.cos(a) * sp, vy=math.sin(a) * sp - 80, g=260,
                life=1.3, max=1.3, col=random.choice(PALETTE), kind="heart",
                size=random.uniform(0.35, 0.8)))

    def firework(self, x, y):
        col = random.choice(PALETTE[:6])
        for _ in range(70):
            a = random.uniform(0, 6.28)
            sp = random.uniform(70, 270)
            self.sparks.append(dict(
                x=x, y=y, vx=math.cos(a) * sp, vy=math.sin(a) * sp, g=140,
                life=random.uniform(1.0, 1.8), max=1.8,
                col=col if random.random() < 0.8 else "#ffffff",
                kind="dot", size=random.uniform(1.8, 3.8)))

    # ---------------------------- cập nhật --------------------------
    def update(self, dt):
        now = time.time()

        # Gõ chữ
        if self.stage == "intro":
            line = self.lines[self.li]
            if self.hold_until is None:
                self.ci += 16 * dt
                if self.ci >= len(line):
                    self.ci = len(line)
                    self.hold_until = now + 1.5
            elif now >= self.hold_until:
                self.hold_until = None
                if self.li < len(self.lines) - 1:
                    self.li += 1
                    self.ci = 0
                else:
                    self.stage = "ask"
        elif self.stage == "ask":
            self.qi = min(len(self.question), self.qi + 16 * dt)

        # Tim bay lên
        rate = {"intro": 4, "ask": 7, "yes": 16}[self.stage]
        self.spawn_acc += rate * dt
        while self.spawn_acc >= 1:
            self.spawn_acc -= 1
            self.spawn_heart()
        for h in self.hearts:
            h["y"] -= h["v"] * dt
        self.hearts = [h for h in self.hearts if h["y"] > -40]

        # Pháo hoa
        if self.stage == "yes" and self.t >= self.next_fw:
            self.firework(random.uniform(80, W - 80), random.uniform(70, 360))
            self.next_fw = self.t + random.uniform(0.25, 0.7)
        for p in self.sparks:
            p["vy"] += p["g"] * dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
        self.sparks = [p for p in self.sparks if p["life"] > 0]

    # ------------------------------ vẽ ------------------------------
    def text(self, x, y, s, size, color="#ffffff", style="bold", **kw):
        font = ("Arial", size, style)
        self.c.create_text(x + 2, y + 2, text=s, font=font, fill="#1a0a22",
                           width=W - 90, justify="center", **kw)
        self.c.create_text(x, y, text=s, font=font, fill=color,
                           width=W - 90, justify="center", **kw)

    def rrect(self, box, r, **kw):
        x1, y1, x2, y2 = box
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        self.c.create_polygon(pts, smooth=True, **kw)

    def draw_stars(self):
        for x, y, r, ph in self.stars:
            a = 0.25 + 0.75 * (0.5 + 0.5 * math.sin(self.t * 1.6 + ph))
            self.c.create_oval(x - r, y - r, x + r, y + r, outline="",
                               fill=mix(BG, "#ffffff", a * 0.8))

    def draw_main_heart(self):
        period = {"intro": 0.9, "ask": 0.75, "yes": 0.5}[self.stage]
        p = (self.t % period) / period
        k = math.exp(-((p - 0.08) / 0.05) ** 2) + 0.7 * math.exp(-((p - 0.30) / 0.06) ** 2)
        base = 9.0 if self.stage == "yes" else 8.0
        s = base * (1 + (0.10 if self.stage == "yes" else 0.08) * k)
        cx, cy = W / 2, 235
        if self.stage == "yes":
            cy += 8 * math.sin(self.t * 6)

        for i in range(7, 0, -1):                       # hào quang
            self.c.create_polygon(
                heart_poly(cx, cy, s * (1 + 0.035 * i)), outline="",
                fill=mix(BG, "#ff2e63", 0.035 * (8 - i) + 0.02 * k))
        self.c.create_polygon(heart_poly(cx, cy, s), fill="#d4123a",
                              outline="#ffd6dd", width=2)
        self.c.create_polygon(heart_poly(cx, cy, s, 0.82, -1.0, 1.8),
                              fill="#ff3d63", outline="")
        self.c.create_polygon(heart_poly(cx, cy, s, 0.52, -2.3, 3.0),
                              fill="#ff8fa3", outline="")
        self.c.create_polygon(heart_poly(cx, cy, s, 0.22, -3.6, 4.3),
                              fill="#ffe0e6", outline="")

    def draw_particles(self):
        for h in self.hearts:
            x = h["x0"] + h["amp"] * math.sin(h["ph"] + self.t * h["f"])
            a = 0.35 + 0.65 * min(1, h["y"] / 120 + 0.2)
            self.c.create_polygon(heart_poly(x, h["y"], 0.9 * h["s"], small=True),
                                  fill=mix(BG, h["col"], a), outline="")
        for p in self.sparks:
            f = p["life"] / p["max"]
            col = mix(BG, p["col"], f)
            if p["kind"] == "dot":
                r = p["size"] * (0.4 + 0.6 * f)
                self.c.create_oval(p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r,
                                   fill=col, outline="")
            else:
                self.c.create_polygon(heart_poly(p["x"], p["y"], p["size"] * 1.4, small=True),
                                      fill=col, outline="")

    def draw_texts(self):
        self.text(W / 2, 40, self.ban + " gửi " + self.ten, 20, "#ff9db1", "italic")
        if self.stage == "intro":
            s = self.lines[self.li][:int(self.ci)]
            self.text(W / 2, 480, s + ("▌" if int(self.t * 2) % 2 == 0 else ""), 21)
        elif self.stage == "ask":
            self.text(W / 2, 470, self.question[:int(self.qi)], 25, "#ffd1dc")
        else:
            dt = self.t - self.yes_t
            pulse = 1 + 0.04 * math.sin(self.t * 8)
            self.text(W / 2, 470, self.final[0], int(30 * pulse), "#ffd1dc")
            if dt > 1.2:
                self.text(W / 2, 535, self.final[1], 20)
            if dt > 2.4:
                self.text(W / 2, 600, "— " + self.ban + " ♥", 22, "#ff9db1", "italic")

    def draw_buttons(self):
        yb = self.yes_box()
        hover = self.inside(yb, self.mx, self.my)
        self.rrect((yb[0] + 3, yb[1] + 4, yb[2] + 3, yb[3] + 4), 24 * self.yes_scale,
                   fill="#1a0a22", outline="")
        self.rrect(yb, 24 * self.yes_scale,
                   fill="#ff5c82" if hover else "#ff2e63", outline="#ffd6dd", width=2)
        self.c.create_text((yb[0] + yb[2]) / 2, (yb[1] + yb[3]) / 2,
                           text="Đồng ý ♥", fill="white",
                           font=("Arial", int(16 * self.yes_scale), "bold"))
        nb = self.no_box()
        self.rrect(nb, 22, fill="#3a3550", outline="#6d6788", width=2)
        self.c.create_text(self.no_c[0], self.no_c[1], text=self.no_label,
                           fill="#d9d4ee", font=("Arial", 14, "bold"))

    def draw(self):
        self.c.delete("all")
        self.draw_stars()
        self.draw_main_heart()
        self.draw_particles()
        self.draw_texts()
        if self.stage == "ask":
            self.draw_buttons()

    def tick(self):
        now = time.time()
        dt = min(now - self.last, 0.05)
        self.last = now
        self.t = now - self.t0
        self.update(dt)
        self.draw()
        self.root.after(16, self.tick)


def main():
    ten = sys.argv[1] if len(sys.argv) > 1 else TEN_NGUOI_AY
    ban = sys.argv[2] if len(sys.argv) > 2 else TEN_BAN
    root = tk.Tk()
    LoveApp(root, ten, ban)
    root.mainloop()


if __name__ == "__main__":
    main()