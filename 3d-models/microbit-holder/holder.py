"""歯ブラシ用 micro:bit グリップホルダー（単4×2 電池ボックス内蔵）

座標（mm）: X = 幅, Y = 厚み（0 が背面、+Y が micro:bit の面）, Z = 高さ（歯ブラシの軸、印刷時の上方向）
出力: holder_body.stl（本体・立てて印刷）, holder_lid.stl（背面のスライドふた・寝かせて印刷）,
      holder_cover.stl（micro:bit の防水カバー・前面を下にして印刷）
実行: python holder.py   （要: pip install manifold3d numpy）
"""
import os
import numpy as np
from manifold3d import Manifold, CrossSection, JoinType

# ---- 測って変える寸法 -------------------------------------------------
BAT = (34.0, 18.0, 68.0)       # 電池ボックス 幅 X, 厚み Y, 長さ Z
BAT_GAP = 1.0                  # 電池ボックスとのすき間（合計。片側 0.5）
HANDLE_W, HANDLE_T = 11.0, 6.0 # 歯ブラシの持ち手の断面（いちばん広い幅, 厚み）。実測: 幅 9〜11, 厚み 6
# 持ち手はまっすぐな部分が下端から 88mm（そこに出っ張り）。差し込みはその範囲内に収める
HANDLE_GAP = 0.4
SOCKET_DEPTH = 30.0            # 持ち手を差し込む深さ
MB_W, MB_H, MB_PCB = 51.6, 42.0, 1.6  # micro:bit V2 公式寸法（51.60 × 42.00, 全厚 11.65）
# ---- 構造 -------------------------------------------------------------
WALL = 2.4
R = 4.0                        # 外形の角の丸み
LIP = 1.2                      # ふたレールの押さえ（背面）
LID_T = 2.0
LID_GAP = 0.3
RAIL = 1.5                     # レール溝の片側の張り出し
FRONT_WALL = 2.0
MB_CLEAR = 5.0                 # 裏面部品の逃げ（Tinkercad のケースは 4.5 で実績あり。少し余裕を足す）
MB_SLOT = MB_PCB + 0.4
MB_LIP = 1.2                   # micro:bit 左右の縁を押さえるつめ
MB_LEDGE = 1.9                 # micro:bit 左右の縁の掛かり（Tinkercad のケースと同じ内幅 49.0）
WIRE_ROOM = 6.6                # 電池の上に配線をまとめる空間
TOP_W, TOP_T = 22.0, 16.0      # 首（先端）の外形
LID_WINDOW = False              # ふたの窓（スイッチが背面にあり、水より操作性を優先するなら True）
# ---- micro:bit 防水カバー（下から差し込み、底の M3 ねじ 2 本で留める） -----------
COVER_GAP = 0.2                # 本体とのすき間（片側）
COVER_SIDE, COVER_FRONT, COVER_FLOOR = 1.6, 3.6, 2.0
COVER_H = 48.0                 # 本体の下端から覆う高さ
COVER_WRAP = 22.0              # 前面から背面方向へ回り込む深さ
MEMBRANE = 0.6                 # LED 窓の厚み（0.2mm 積層で 3 層）
BTN_H = 5.0                    # 基板の表面から A/B ボタンの頂上まで（実測 4.5〜5）。ボタンは使わないのでカバーで隠す
COVER_SKIN = 1.6               # ボタンの上に残すカバーの厚み
BTN_X = 18.5                   # 基板中心から A/B ボタン中心までの横距離
LED_WIN = 23.0                 # LED 窓の一辺

pw, pt, ph = BAT[0] + BAT_GAP, BAT[1] + BAT_GAP, BAT[2] + BAT_GAP
y_groove0 = LIP
y_pocket0 = LIP + LID_T + LID_GAP
y_pocket1 = y_pocket0 + pt
y_cav0 = y_pocket1 + FRONT_WALL
y_slot0 = y_cav0 + MB_CLEAR
y_slot1 = y_slot0 + MB_SLOT
T = y_slot1 + MB_LIP                          # 本体の厚み
slot_w = MB_W + 1.2                           # 52.8: Tinkercad のケースの実測と同じ
W = slot_w + 2 * WALL                         # 本体の幅
z_pocket0 = WALL
z_pocket1 = z_pocket0 + ph + WIRE_ROOM
z_body = z_pocket1 + 3.0                      # 胴体の高さ（ここから首がすぼまる）
H = z_body + SOCKET_DEPTH + 4.0               # 全高
bay_h = MB_H + 0.8


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def rrect(w, t, r, h, cx=0.0, cy=0.0, z0=0.0):
    cs = CrossSection.square((w - 2 * r, t - 2 * r), center=True).offset(r, JoinType.Round, circular_segments=48)
    return cs.extrude(h).translate((cx, cy, z0))


def stadium(w, t, h, cx, cy, z0):
    r = min(w, t) / 2
    return rrect(w, t, r - 0.001, h, cx, cy, z0)


cy = T / 2
outer = rrect(W, T, R, z_body, 0, cy, 0)
neck = Manifold.batch_hull([
    rrect(W, T, R, 0.01, 0, cy, z_body - 6),
    rrect(TOP_W, TOP_T, 6.0, 0.01, 0, cy, H - 0.01),
])
body = outer + neck

cuts = [
    # 電池ポケット（背面が開口）
    box(-pw / 2, pw / 2, 0, y_pocket1, z_pocket0, z_pocket1),
    # ふたのレール溝（下端から差し込む）
    box(-pw / 2 - RAIL, pw / 2 + RAIL, y_groove0, y_pocket0, -1, z_pocket0 + ph),
    box(-pw / 2, pw / 2, -1, y_pocket0, -1, z_pocket0 + 0.01),
    # micro:bit ベイ（下からスライドして差し込む）
    box(-slot_w / 2 + MB_LEDGE, slot_w / 2 - MB_LEDGE, y_cav0, T + 1, -1, bay_h),
    box(-slot_w / 2, slot_w / 2, y_slot0, y_slot1, -1, bay_h),
    # 配線の通り道（電池の上 → micro:bit 裏の電池コネクタ）
    box(-20, 20, y_pocket1 - 1, y_cav0 + 0.5, bay_h - 14, bay_h - 1),
    box(-4, 4, y_pocket1 - 2, y_cav0 + 0.5, bay_h - 14, z_pocket1),
    # 歯ブラシの差し込み穴
    stadium(HANDLE_W + HANDLE_GAP, HANDLE_T + HANDLE_GAP, SOCKET_DEPTH + 1, 0, cy, H - SOCKET_DEPTH),
    # 固定ねじ穴（M3 タッピング用 φ2.6）。幅 9〜11mm のばらつきは横のねじ、厚み方向は前のねじで押さえる
    Manifold.cylinder(TOP_W, 1.3, circular_segments=24).rotate((0, 90, 0)).translate((0, cy, H - 10)),
    Manifold.cylinder(TOP_T, 1.3, circular_segments=24).rotate((-90, 0, 0)).translate((0, cy, H - 22)),
    # カバー固定ねじの下穴（底面から）
    *[Manifold.cylinder(12, 1.3, circular_segments=24).translate((sx, T - 16, -1)) for sx in (-23, 23)],
]
for c in cuts:
    body = body - c

# ---- ふた（寝かせて印刷: 厚み方向を Z に） --------------------------------
lid_w = pw + 2 * RAIL - 2 * LID_GAP
lid_h = z_pocket0 + ph - LID_GAP
lid = box(-lid_w / 2, lid_w / 2, 0, lid_h, 0, LID_T)
if LID_WINDOW:
    lid = lid - rrect(22, 38, 3, LID_T + 2, 0, lid_h / 2 + 4, -1)   # スイッチ確認用の窓
for i in range(3):                                             # 指を掛ける溝
    lid = lid + box(-10, 10, 3 + i * 2.2, 4 + i * 2.2, LID_T, LID_T + 0.8)

# ---- micro:bit 防水カバー（本体と同じ座標で作り、最後に前面を下にして出力） ------------
mb_z = bay_h - MB_H / 2                     # micro:bit は上端に突き当てた位置
y_in = T + COVER_GAP
y_btn = y_slot1 + BTN_H                     # ボタン頂上（基板が一番前に寄った場合）
# ボタンの頂上より 0.5mm 前にくぼみの底、その外にカバーの皮
COVER_FRONT = max(COVER_FRONT, y_btn + 0.5 + COVER_SKIN - y_in)
y_out = y_in + COVER_FRONT
y_mem = y_out - MEMBRANE
cover = rrect(W + 2 * (COVER_GAP + COVER_SIDE), T + 2 * (COVER_GAP + COVER_FRONT), R + COVER_GAP + COVER_SIDE,
              COVER_H + COVER_FLOOR, 0, cy, -COVER_FLOOR)
cover = cover ^ box(-W, W, T - COVER_WRAP, T + 20, -10, COVER_H + 1)
cover = cover - rrect(W + 2 * COVER_GAP, T + 2 * COVER_GAP, R + COVER_GAP, COVER_H + 10, 0, cy, 0)
along_y = lambda h, r: Manifold.cylinder(h, r, circular_segments=40).rotate((-90, 0, 0))
cover = cover - box(-LED_WIN / 2, LED_WIN / 2, y_in - 1, y_mem, mb_z + 1.5 - LED_WIN / 2, mb_z + 1.5 + LED_WIN / 2)
for bx in (-BTN_X, BTN_X):
    cover = cover - along_y(y_btn + 0.5 - y_in + 1, 5.5).translate((bx, y_in - 1, mb_z + 1))  # ボタンの逃げ（押せない）
for sx in (-23, 23):
    cover = cover - Manifold.cylinder(COVER_FLOOR + 2, 1.7, circular_segments=24).translate((sx, T - 16, -COVER_FLOOR - 1))
cover_print = cover.rotate((-90, 0, 0))
cover_print = cover_print.translate((0, 0, -cover_print.bounding_box()[2]))


def save_stl(m, path):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(np.float32)
    f = np.asarray(mesh.tri_verts)
    tri = v[f]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    data = np.zeros(len(f), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    data["n"], data["v"] = n, tri
    with open(path, "wb") as fh:
        fh.write(b"toothbrush microbit holder".ljust(80, b" "))
        fh.write(np.uint32(len(f)).tobytes())
        fh.write(data.tobytes())


if __name__ == "__main__":
    for name, m in [("holder_body.stl", body), ("holder_lid.stl", lid), (os.environ.get("COVER_NAME", "holder_cover.stl"), cover_print)]:
        save_stl(m, name)
        b = m.bounding_box()
        print(f"{name}: {b[3]-b[0]:.1f} x {b[4]-b[1]:.1f} x {b[5]-b[2]:.1f} mm, "
              f"volume {m.volume()/1000:.1f} cm3, genus {m.genus()}")
    save_stl(cover, "_cover_assembled.stl")  # 3D ビューア用（本体と同じ座標）
    print(f"cover front {COVER_FRONT:.2f} mm")
    print(f"body W={W:.1f} T={T:.1f} H={H:.1f}; pocket {pw}x{pt}x{ph}; mb slot z 0..{bay_h}")
