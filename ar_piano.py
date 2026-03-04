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
WHITE_RADIUS = 6 
BLACK_RADIUS = 5
VISIBLE_WHITE_KEYS = 32  
LEFT_MIDI = 48  
# ==========================================

def get_note_name(midi_note):
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

# ペンタトニックに絞り込んだジャズ進行
scenario = [
    {
        "time": 0, 
        "chord": "Dm9 (D Min Pentatonic)", 
        "pitch_classes": [2, 5, 7, 9, 0], 
        "color": (255, 150, 50)  # 青
    },
    {
        "time": 4, 
        "chord": "G7alt (Bb Min Pentatonic)", 
        "pitch_classes": [10, 1, 3, 5, 8], 
        "color": (50, 100, 255)  # 赤・オレンジ
    },
    {
        "time": 8, 
        "chord": "Cmaj9 (C Maj Pentatonic)", 
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
    # 「次のコード」を取得
    next_state = scenario[(current_idx + 1) % len(scenario)]

    overlay = img.copy()

    for midi_note in range(LEFT_MIDI - 5, LEFT_MIDI + 65):
        x, y, is_black, rel_white_idx = get_key_pos(midi_note)
        
        if 0 <= rel_white_idx <= VISIBLE_WHITE_KEYS and START_X <= x <= END_X + 15:
            r = BLACK_RADIUS if is_black else WHITE_RADIUS
            note_name = get_note_name(midi_note)
            pitch_class = midi_note % 12
            
            is_current = pitch_class in current_state["pitch_classes"]
            is_next = pitch_class in next_state["pitch_classes"]
            
            # --- 描画の優先順位（UIの階層化） ---
            
            if is_current:
                # 1. 今のコード（最も目立つ：鮮やかなベタ塗り＋白いコア）
                cv2.circle(overlay, (x, y), r + 2, current_state["color"], cv2.FILLED)
                cv2.circle(overlay, (x, y), int(r * 0.5), (255, 255, 255), cv2.FILLED)
                cv2.putText(overlay, note_name, (x - 12, y - 15), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
                            
            elif is_next:
                # 2. 次のコードの予兆（控えめ：次の色の細いリングのみ）
                # 色を少し暗くする計算
                dim_color = tuple(int(c * 0.7) for c in next_state["color"])
                cv2.circle(overlay, (x, y), r, dim_color, 2) # 太さ2のリング
                cv2.putText(overlay, note_name, (x - 10, y - 12), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.3, dim_color, 1)
                            
            else:
                # 3. どちらでもない関係ない音（極薄グレーで背景に溶け込ませる）
                cv2.circle(overlay, (x, y), r, (70, 70, 70), 1)

    alpha = 0.8
    img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

    # 画面上部のUIテキストも「今」と「次」を表示
    cv2.putText(img, f"Now Playing: {current_state['chord']}", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, current_state["color"], 2)
    cv2.putText(img, f"Next (Prep): {next_state['chord']}", (20, 75), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, next_state["color"], 1)

    cv2.imshow("AR Jazz Session - Foreshadowing UI", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()