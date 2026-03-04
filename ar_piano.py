import cv2
import time

# Iriun Webcamのカメラ番号
cap = cv2.VideoCapture(1)

# ==========================================
# 🔴 キャリブレーション設定（ここを微調整してください）
# ==========================================
# 1. ピアノの左右の位置
START_X = 0   # 画面一番左の「白鍵」の左端X座標
END_X = 700    # 画面一番右の「白鍵」の右端X座標

# 2. 指で弾く位置の高さ（この高さに横線が引かれます）
WHITE_Y = 300  # 白鍵の丸の高さ（赤線）
BLACK_Y = 270  # 黒鍵の丸の高さ（緑線）

# 3. 丸の大きさ
WHITE_RADIUS = 6
BLACK_RADIUS = 5

# 4. 画角の調整
VISIBLE_WHITE_KEYS = 32  # 画面に収まっている白鍵の数
LEFT_MIDI = 48           # 画面の一番左端に映っている白鍵のMIDIノート番号（例：C3=48）
# ==========================================

def get_white_idx_and_is_black(midi_note):
    """MIDIノートが何番目の白鍵グループか、黒鍵かどうかを判定"""
    octave = midi_note // 12
    note_in_octave = midi_note % 12
    
    # C=0, C#=0, D=1, D#=1, E=2, F=3, F#=3, G=4, G#=4, A=5, A#=5, B=6
    white_offsets = [0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6]
    is_black_list = [False, True, False, True, False, False, True, False, True, False, True, False]
    
    abs_white_idx = octave * 7 + white_offsets[note_in_octave]
    is_black = is_black_list[note_in_octave]
    return abs_white_idx, is_black

def get_key_pos(midi_note):
    """黒鍵・白鍵の物理的な配置に基づく正確なピクセル座標を計算"""
    left_abs_idx, _ = get_white_idx_and_is_black(LEFT_MIDI)
    abs_white_idx, is_black = get_white_idx_and_is_black(midi_note)
    
    # 画面左端の白鍵を0としたときの相対位置
    rel_white_idx = abs_white_idx - left_abs_idx
    key_width = (END_X - START_X) / VISIBLE_WHITE_KEYS
    
    # 白鍵の中心は幅の真ん中(+0.5)、黒鍵は白鍵と白鍵の境界線上(+1.0)
    visual_idx = rel_white_idx + 1.0 if is_black else rel_white_idx + 0.5
    
    x = int(START_X + visual_idx * key_width)
    y = BLACK_Y if is_black else WHITE_Y
    
    return x, y, is_black, rel_white_idx

while True:
    success, img = cap.read()
    if not success:
        break

    overlay = img.copy()

    # --- キャリブレーション用の補助線 ---
    cv2.line(overlay, (START_X, WHITE_Y), (END_X, WHITE_Y), (0, 0, 255), 1) # 白鍵の高さ（赤線）
    cv2.line(overlay, (START_X, BLACK_Y), (END_X, BLACK_Y), (0, 255, 0), 1) # 黒鍵の高さ（緑線）
    
    # 左端と右端の垂直線（この線の間に32個の白鍵が収まるようにする）
    cv2.line(overlay, (START_X, 0), (START_X, img.shape[0]), (255, 255, 0), 1) # 左端（水色）
    cv2.line(overlay, (END_X, 0), (END_X, img.shape[0]), (255, 255, 0), 1)     # 右端（水色）
    # ------------------------------------

    # 画面内に映る範囲のすべての鍵盤（LEFT_MIDIから約60半音分）を描画
    for midi_note in range(LEFT_MIDI, LEFT_MIDI + 60):
        x, y, is_black, rel_white_idx = get_key_pos(midi_note)
        
        # 画面内に収まっているものだけを描画
        if 0 <= rel_white_idx <= VISIBLE_WHITE_KEYS and x <= END_X + 15:
            r = BLACK_RADIUS if is_black else WHITE_RADIUS
            
            # すべてグレーで描画
            cv2.circle(overlay, (x, y), r, (150, 150, 150), cv2.FILLED)
            
            # 視認性を高めるための縁取り（白鍵は明るめ、黒鍵は暗め）
            if is_black:
                cv2.circle(overlay, (x, y), r, (80, 80, 80), 1)
            else:
                cv2.circle(overlay, (x, y), r, (200, 200, 200), 1)

    # 合成（透明度0.7）
    alpha = 0.7
    img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

    cv2.putText(img, "Calibration Mode: All Keys", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    cv2.imshow("AR Jazz Session - Calibration", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()