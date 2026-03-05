import cv2
import time

cap = cv2.VideoCapture(1)

# ==========================================
# 🔴 あなたのキャリブレーション設定を入れてください
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

FALL_SPEED = 150
BAR_WIDTH_ADJUST = 0.8

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
    return x, y, is_black, rel_white_idx, key_width

# === LLMによるアレンジ生成を模した3つのパターン ===

# パターン1：Normal (標準)
melody_normal = [
    {"time": 2.0, "note": 60, "duration": 0.5}, {"time": 2.5, "note": 60, "duration": 0.5},
    {"time": 3.0, "note": 67, "duration": 0.5}, {"time": 3.5, "note": 67, "duration": 0.5},
    {"time": 4.0, "note": 69, "duration": 0.5}, {"time": 4.5, "note": 69, "duration": 0.5},
    {"time": 5.0, "note": 67, "duration": 1.0},
]

# パターン2：Super Easy (超初心者向け・ゆっくり単音)
melody_easy = [
    {"time": 2.0, "note": 60, "duration": 1.0}, # ド (ゆっくり)
    {"time": 4.0, "note": 67, "duration": 1.0}, # ソ
    {"time": 6.0, "note": 69, "duration": 1.0}, # ラ
]

# パターン3：Jazz Bossa (ジャズアレンジ・和音と裏拍)
melody_jazz = [
    {"time": 2.0, "note": 60, "duration": 0.5}, {"time": 2.5, "note": 60, "duration": 0.5},
    {"time": 3.0, "note": 67, "duration": 0.5}, {"time": 3.5, "note": 67, "duration": 0.5},
    {"time": 3.75, "note": 59, "duration": 0.25}, {"time": 3.75, "note": 64, "duration": 0.25}, # 合いの手
    {"time": 4.0, "note": 69, "duration": 0.5}, {"time": 4.5, "note": 69, "duration": 0.5},
    {"time": 5.0, "note": 67, "duration": 1.0},
    {"time": 5.5, "note": 55, "duration": 0.5}, {"time": 5.5, "note": 62, "duration": 0.5}, # 合いの手
]

# 初期状態
current_melody = melody_normal
prompt_text = "Prompt: Normal"
prompt_color = (255, 255, 255)

is_playing = False
start_time = 0

while True:
    success, img = cap.read()
    if not success:
        break

    if not is_playing:
        cv2.putText(img, "Press 1:Normal, 2:Easy, 3:Jazz  (SPACE to Start)", (20, 100), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.imshow("AR Piano - LLM Prompt Arranger", img)
        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):
            is_playing = True
            start_time = time.time()
        elif key == ord('q'):
            break
        continue

    current_time = time.time() - start_time
    overlay = img.copy()

    # ヒットライン
    cv2.line(overlay, (START_X, WHITE_Y), (END_X, WHITE_Y), (255, 255, 255), 1)

    # 降ってくるバーの描画処理
    for item in current_melody:
        note_time = item["time"]
        note_duration = item["duration"]
        midi_note = item["note"]
        
        x, hit_y, is_black, rel_white_idx, key_width = get_key_pos(midi_note)
        
        if 0 <= rel_white_idx <= VISIBLE_WHITE_KEYS and START_X <= x <= END_X + 15:
            bar_bottom_y = hit_y - int((note_time - current_time) * FALL_SPEED)
            bar_top_y = bar_bottom_y - int(note_duration * FALL_SPEED)
            
            if bar_bottom_y > 0 and bar_top_y < img.shape[0]:
                if note_time <= current_time <= note_time + note_duration:
                    color = (100, 255, 100) # 発光
                    cv2.circle(overlay, (x, hit_y), 15, color, cv2.FILLED)
                else:
                    color = (255, 200, 50)
                
                bar_w = int(key_width * BAR_WIDTH_ADJUST)
                x1 = x - bar_w // 2
                x2 = x + bar_w // 2
                
                cv2.rectangle(overlay, (x1, max(0, bar_top_y)), (x2, bar_bottom_y), color, cv2.FILLED)
                cv2.rectangle(overlay, (x1, max(0, bar_top_y)), (x2, bar_bottom_y), (255, 255, 255), 1)

    alpha = 0.7
    img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
    
    # AIがアレンジしている感を出すUIテキスト
    cv2.putText(img, "AI Style-Transfer Mode", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
    cv2.putText(img, prompt_text, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, prompt_color, 2)

    cv2.imshow("AR Piano - LLM Prompt Arranger", img)

    # キーボード入力で「プロンプト」を切り替え、時間をリセット
    key = cv2.waitKey(1) & 0xFF
    if key == ord('1'):
        current_melody = melody_normal
        prompt_text = 'Prompt: "Play normally"'
        prompt_color = (255, 255, 255)
        start_time = time.time()
    elif key == ord('2'):
        current_melody = melody_easy
        prompt_text = 'Prompt: "Make it Super Easy for beginners"'
        prompt_color = (50, 255, 100)
        start_time = time.time()
    elif key == ord('3'):
        current_melody = melody_jazz
        prompt_text = 'Prompt: "Arrange it like a Jazz Bossa Nova"'
        prompt_color = (100, 100, 255)
        start_time = time.time()
    elif key == ord('q'):
        break

    # ループ処理
    if current_time > 8:
        start_time = time.time()

cap.release()
cv2.destroyAllWindows()