import cv2
import mediapipe as mp
from mediapipe import Image
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

# MediaPipeの手の認識AIを準備（新しいAPI）
# モデルファイルを自動ダウンロード
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=2)
detector = vision.HandLandmarker.create_from_options(options)

# Webカメラの準備（0番目のカメラ）
cap = cv2.VideoCapture(0)

# 画面上に作る「仮想の鍵盤（パレット）」の座標 (x1, y1, x2, y2)
key_x1, key_y1 = 200, 250
key_x2, key_y2 = 400, 350

print("カメラを起動しています...（終了するには画面上で 'q' キーを押してください）")

while True:
    success, img = cap.read()
    if not success:
        break

    # 鏡のように反転させる（操作しやすくするため）
    img = cv2.flip(img, 1)
    h, w, c = img.shape

    # AIに画像を渡して手を認識させる
    rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mp_image = Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
    detection_result = detector.detect(mp_image)

    # デフォルトの鍵盤の色は「青（待機中・提案パレット）」
    key_color = (255, 100, 100) # BGRの順番です (青っぽく光る)
    text = "Palette: Jazz Scale"

    # もし手が画面内に見つかったら
    if detection_result.hand_landmarks:
        for hand_landmarks in detection_result.hand_landmarks:
            # 人差し指の先端（8番目のランドマーク）の座標を取得
            index_finger = hand_landmarks[8]
            cx = int(index_finger.x * w)
            cy = int(index_finger.y * h)

            # 人差し指の先に赤い丸を描画
            cv2.circle(img, (cx, cy), 15, (0, 0, 255), cv2.FILLED)

            # 当たり判定：人差し指が「仮想の鍵盤」の中に入ったか？
            if key_x1 < cx < key_x2 and key_y1 < cy < key_y2:
                # 触れたら「オレンジ色」に光らせて、文字を変える！
                key_color = (0, 165, 255) # オレンジ色
                text = "PLAYING! (Session...)"

    # 仮想の鍵盤（四角形）を画面に描画
    cv2.rectangle(img, (key_x1, key_y1), (key_x2, key_y2), key_color, cv2.FILLED)
    
    # 枠線を少し濃く描画してホログラム感を出す
    cv2.rectangle(img, (key_x1, key_y1), (key_x2, key_y2), (255, 255, 255), 3)

    # テキストを画面に表示
    cv2.putText(img, text, (key_x1, key_y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    # 結果を画面に表示
    cv2.imshow("AR Jazz Session - Prototype", img)

    # 'q' キーが押されたら終了
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()