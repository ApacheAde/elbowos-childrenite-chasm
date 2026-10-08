#!/usr/bin/env python3
"""Childrenite Chasm — portrait neon wall-kick climber for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/CHILDRENITE_CHASM_ElbowOS.mp4")
TITLE, HANDLE = "CHILDRENITE CHASM", "x.com/ElbowOS"
INK, LIME, VIO, AMBER, MAG, WHITE = (4, 14, 12), (120, 255, 70), (190, 70, 255), (255, 186, 40), (255, 50, 120), (240, 255, 230)

class Game:
    def __init__(self):
        pygame.init(); pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        self.font = pygame.font.SysFont("arial", 64, bold=True)
        self.small = pygame.font.SysFont("arial", 36, bold=True)
        self.tiny = pygame.font.SysFont("arial", 28, bold=True)
        self.reset()

    def reset(self):
        self.t = 0
        self.score = 0
        self.combo = 1
        self.px, self.py, self.vx = W / 2, 1180, 11
        self.flash = 0
        self.shards = []
        self.motes = [[random.randrange(80, W - 80), random.randrange(0, H), random.choice((LIME, VIO, AMBER))] for _ in range(40)]
        self.gems = []
        self.spikes = []
        self.seed_lane()

    def seed_lane(self):
        self.lane = []
        y = -200
        left = 180
        while y < H + 400:
            left = max(70, min(430, left + random.randint(-70, 70)))
            gap = random.randint(340, 520)
            self.lane.append([y, left, left + gap])
            y += 90

    def gap_at(self, y):
        best = self.lane[0]
        for seg in self.lane:
            if seg[0] <= y:
                best = seg
            else:
                break
        return best[1], best[2]

    def burst(self, x, y, col, n=10):
        for _ in range(n):
            a = random.random() * math.tau
            s = random.uniform(2, 9)
            self.shards.append([x, y, math.cos(a) * s, math.sin(a) * s, 18, col])

    def update(self, steer=0):
        self.t += 1
        scroll = 7 + self.t / 180
        for seg in self.lane:
            seg[0] += scroll
        self.lane = [s for s in self.lane if s[0] < H + 240]
        if not self.lane:
            self.lane = [[-180, 160, 640]]
        while self.lane[-1][0] < H + 280:
            prev = self.lane[-1]
            left = max(70, min(430, prev[1] + random.randint(-80, 80)))
            gap = random.randint(320, 500)
            self.lane.append([prev[0] + 90, left, left + gap])
        if self.t % 18 == 0:
            gy = -40
            L, R = self.gap_at(200)
            self.gems.append([random.uniform(L + 40, R - 40), gy, AMBER if random.random() < 0.7 else WHITE])
        if self.t % 28 == 0:
            side = random.choice((-1, 1))
            self.spikes.append([side, random.uniform(-80, 200)])
        for g in self.gems:
            g[1] += scroll
        for s in self.spikes:
            s[1] += scroll
        self.gems = [g for g in self.gems if g[1] < H + 40]
        self.spikes = [s for s in self.spikes if s[1] < H + 40]
        L, R = self.gap_at(self.py)
        target = (L + R) / 2
        near = [g for g in self.gems if 700 < g[1] < 1400]
        if near:
            target = min(near, key=lambda g: abs(g[1] - self.py))[0]
        if steer:
            target = self.px + steer * 180
        self.px += (target - self.px) * 0.16
        if self.px < L + 28:
            self.px = L + 28
            self.vx = abs(self.vx) + 1
            self.burst(self.px, self.py, LIME, 6)
            self.combo = min(8, self.combo + 0.05)
        if self.px > R - 28:
            self.px = R - 28
            self.vx = -abs(self.vx) - 1
            self.burst(self.px, self.py, VIO, 6)
        for g in self.gems:
            if (g[0] - self.px) ** 2 + (g[1] - self.py) ** 2 < 46 ** 2:
                self.score += int(25 * self.combo)
                self.burst(g[0], g[1], g[2], 14)
                g[1] = 9999
                self.flash = 8
        self.gems = [g for g in self.gems if g[1] < H + 30]
        hit = None
        for sp in self.spikes:
            side, sy = sp
            sx = (self.gap_at(sy)[0] + 18) if side < 0 else (self.gap_at(sy)[1] - 18)
            if abs(sx - self.px) < 36 and abs(sy - self.py) < 36:
                hit = sp
                break
        if hit:
            self.score = max(0, self.score - 15)
            self.combo = 1
            self.flash = 10
            self.burst(self.px, self.py, MAG, 12)
            self.spikes.remove(hit)
        for m in self.motes:
            m[1] = (m[1] + scroll * 0.45) % H
        for sh in self.shards:
            sh[0] += sh[2]; sh[1] += sh[3]; sh[3] += 0.15; sh[4] -= 1
        self.shards = [s for s in self.shards if s[4] > 0]
        if self.flash:
            self.flash -= 1

    def draw(self, surf):
        surf.fill(INK)
        for i, m in enumerate(self.motes):
            pygame.draw.circle(surf, m[2], (int(m[0]), int(m[1])), 2 + i % 3)
        for y, L, R in self.lane:
            pygame.draw.rect(surf, (18, 60, 28), (0, int(y), int(L), 86))
            pygame.draw.rect(surf, LIME, (int(L) - 10, int(y), 10, 86))
            pygame.draw.rect(surf, (48, 16, 70), (int(R), int(y), W - int(R), 86))
            pygame.draw.rect(surf, VIO, (int(R), int(y), 10, 86))
        for side, sy in self.spikes:
            L, R = self.gap_at(sy)
            sx = L + 8 if side < 0 else R - 8
            pts = [(sx, sy - 22), (sx + side * -26, sy), (sx, sy + 22)]
            pygame.draw.polygon(surf, MAG, pts)
        for gx, gy, col in self.gems:
            pts = [(gx, gy - 18), (gx + 14, gy), (gx, gy + 18), (gx - 14, gy)]
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, WHITE, pts, 2)
        bob = math.sin(self.t / 5) * 6
        pygame.draw.circle(surf, (180, 255, 160), (int(self.px), int(self.py + bob)), 34)
        pygame.draw.circle(surf, WHITE, (int(self.px), int(self.py + bob)), 16)
        if self.flash:
            pygame.draw.circle(surf, AMBER, (int(self.px), int(self.py)), 48, 3)
        for x, y, vx, vy, life, col in self.shards:
            pygame.draw.circle(surf, col, (int(x), int(y)), max(1, life // 5))
        banner = pygame.Surface((W, 150), pygame.SRCALPHA)
        banner.fill((0, 0, 0, 140))
        surf.blit(banner, (0, 0))
        surf.blit(self.font.render(TITLE, True, LIME), (36, 28))
        surf.blit(self.small.render(f"SCORE {self.score}", True, AMBER), (40, 100))
        foot = pygame.Surface((W, 90), pygame.SRCALPHA)
        foot.fill((0, 0, 0, 150))
        surf.blit(foot, (0, H - 90))
        surf.blit(self.tiny.render(HANDLE, True, WHITE), (W // 2 - 120, H - 58))

    def play_interactive(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            steer = 0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                    self.reset()
            keys = pygame.key.get_pressed()
            steer = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
            self.update(steer)
            self.draw(self.screen)
            pygame.display.flip()
            clock.tick(FPS)
        pygame.quit()

    def record(self):
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
               "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", OUT]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        surf = pygame.Surface((W, H))
        try:
            for _ in range(FPS * SECS):
                self.update()
                self.draw(surf)
                proc.stdin.write(pygame.image.tobytes(surf, "RGB"))
        finally:
            proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore")
        rc = proc.wait()
        if rc != 0 or not os.path.isfile(OUT) or os.path.getsize(OUT) < 10000:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
        alt = "/home/workdir/artifacts/" + os.path.basename(OUT)
        os.makedirs("/home/workdir/artifacts", exist_ok=True)
        if os.path.abspath(alt) != os.path.abspath(OUT):
            import shutil
            shutil.copy2(OUT, alt)
        print("wrote", OUT)
        pygame.quit()

def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()

if __name__ == "__main__":
    main()
