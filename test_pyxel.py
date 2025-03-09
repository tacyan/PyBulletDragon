import pyxel

# Pyxelの初期化
pyxel.init(160, 120)

# Soundオブジェクトの作成方法を確認
# バージョン情報の表示
print(f"Pyxel version: {pyxel.VERSION}")

# 音を作成して確認（バージョンによって方法が異なるため）
try:
    # 現在のPyxelバージョンでの音の作成方法を試行
    sound = pyxel.Sound()
    print("Sound created successfully with no arguments")
    
    # 音の設定方法を確認
    sound.set("c3e3g3c4", "s", "4", "n", 7)
    print("Sound.set() worked")
    
    # サウンドバンクに割り当て
    pyxel.sounds[0] = sound
    print("Assigned to sounds[0] successfully")
except Exception as e:
    print(f"Error: {e}")

# プログラム終了前のwait
print("Press CTRL+C to exit")
try:
    while True:
        pyxel.flip()
except KeyboardInterrupt:
    print("Exiting...") 