import cv2
import time

cap = cv2.VideoCapture(1)

# ==========================================
# 🔴 先ほどピッタリ合ったキャリブレーションの数字をここに入れてください
# ==========================================
START_X = 0  
END_X = 700    
WHITE_Y = 300  
BLACK_Y = 270  
WHITE_RADIUS = 6  # 色が目立つように少しだけ大きくしました
BLACK_RADIUS = 5
VISIBLE_WHITE_KEYS = 32  
LEFT_MIDI = 48  
# ==========================================

def get_note_name(midi_note):
    """MIDI番号から音名（C4など）の文字列を生成して返す関数"""
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    name = note_names[midi_note % 12]
    octave = (midi_note // 12) - 1
    return f"{name}{octave}"

def get_white_idx_and_is_black(midi_note):
    octave = midi_note // 12
    note_in_octave = midi_note % 12
    white_offsets = [0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6]
    is_black_list = [False, True, False, True, False, False, True, False, True, False, True, False]
    return octave * 7 + white_offsets[note_in_octave], is_black_list[note_in_octave]

def get_key_pos(midi_note):
    left_abs_idx, _ = get_white_idx_and_is_black(LEFT_MIDI)
    abs_white_idx, is_black = get_white_idx_and_is_black(midi_note)
    
    rel_white_idx = abs_white_idx - left_abs_idx
    key_width = (END_X - START_X) / VISIBLE_WHITE_KEYS
    visual_idx = rel_white_idx + 1.0 if is_black else rel_white_idx + 0.5
    
    x = int(START_X + visual_idx * key_width)
    y = BLACK_Y if is_black else WHITE_Y
    return x, y, is_black, rel_white_idx

# 構成音を7音から5音（ペンタトニック）に厳選し、迷いをなくす
scenario = [
    {
        "time": 0, 
        "chord": "Dm9 (D Min Pentatonic)", 
        # D, F, G, A, C (白鍵の中の5音。絶対に外さない魔法の5音)
        "pitch_classes": [2, 5, 7, 9, 0], 
        "color": (255, 150, 50)  # 青
    },
    {
        "time": 4, 
        "chord": "G7alt (Bb Min Pentatonic)", 
        # Bb, Db, Eb, F, Ab (ジャズの裏技。G7の上でBbマイナーペンタを弾くと超絶オシャレなオルタードになる)
        "pitch_classes": [10, 1, 3, 5, 8], 
        "color": (50, 100, 255)  # 赤・オレンジ系
    },
    {
        "time": 8, 
        "chord": "Cmaj9 (C Maj Pentatonic)", 
        # C, D, E, G, A (明るくスッキリした解決の5音)
        "pitch_classes": [0, 2, 4, 7, 9], 
        "color": (150, 255, 100) # グリーン
    }
]

start_time = time.time()

while True:
    success, img = cap.read()
    if not success:
        break

    elapsed_time = (time.time() - start_time) % 12
    
    current_idx = 0
    for i, state in enumerate(scenario):
        if elapsed_time >= state["time"]:
            current_idx = i
    current_state = scenario[current_idx]

    overlay = img.copy()

    for midi_note in range(LEFT_MIDI - 5, LEFT_MIDI + 65):
        x, y, is_black, rel_white_idx = get_key_pos(midi_note)
        
        # 画面内に収まっている鍵盤だけ処理
        if 0 <= rel_white_idx <= VISIBLE_WHITE_KEYS and START_X <= x <= END_X + 15:
            r = BLACK_RADIUS if is_black else WHITE_RADIUS
            note_name = get_note_name(midi_note)
            pitch_class = midi_note % 12
            
            # この音が「今のコードのスケール」に含まれているか判定
            if pitch_class in current_state["pitch_classes"]:
                # 含まれている場合は鮮やかに光らせる
                cv2.circle(overlay, (x, y), r + 2, current_state["color"], cv2.FILLED)
                cv2.circle(overlay, (x, y), int(r * 0.5), (255, 255, 255), cv2.FILLED)
                
                # 音名を少し上に明るい白で表示（プログラム側の認識証明）
                cv2.putText(overlay, note_name, (x - 12, y - 15), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
            else:
                # 含まれていない音は、薄いグレーでひっそり表示
                cv2.circle(overlay, (x, y), r, (100, 100, 100), 1)
                cv2.putText(overlay, note_name, (x - 10, y - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.3, (150, 150, 150), 1)

    alpha = 0.8
    img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

    # 現在のコード名を大きく表示
    cv2.putText(img, f"Now Playing: {current_state['chord']}", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, current_state["color"], 2)

    cv2.imshow("AR Jazz Session - Note Mapping & Palette", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()