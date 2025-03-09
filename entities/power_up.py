"""
パワーアップアイテムクラスモジュール

ゲーム内のパワーアップアイテムの動作と描画を担当するクラスを定義します。
"""

import pyxel
import math
import random

# パワーアップアイテムの種類
POWER_UP_TYPE_POWER = 0  # パワーアップ
POWER_UP_TYPE_LIFE = 1   # 残機アップ
POWER_UP_TYPE_BOMB = 2   # ボムアップ

class PowerUp:
    """
    パワーアップアイテムクラス
    
    プレイヤーが取得するとパワーアップするアイテムの動作、描画を担当します。
    """
    def __init__(self, x, y, item_type=None):
        """
        パワーアップアイテムを初期化します。
        
        @param {number} x - アイテムのX座標
        @param {number} y - アイテムのY座標
        @param {number} item_type - アイテムの種類（None:ランダム）
        """
        self.x = x
        self.y = y
        self.width = 8
        self.height = 8
        self.base_speed = 1
        self.speed = self.base_speed
        # アイテムの種類をランダムに設定（確率調整）
        if item_type is None:
            rand = random.random()
            if rand < 0.7:  # 70%の確率でパワーアップ
                self.item_type = POWER_UP_TYPE_POWER
            elif rand < 0.9:  # 20%の確率でボムアップ
                self.item_type = POWER_UP_TYPE_BOMB
            else:  # 10%の確率で残機アップ
                self.item_type = POWER_UP_TYPE_LIFE
        else:
            self.item_type = item_type
            
        # 動きに関連する変数
        self.sin_offset = random.uniform(0, math.pi * 2)  # サイン波のオフセット
        self.hover_time = 0  # ホバリング時間
        self.is_homing = False  # 自機追尾フラグ
        self.homing_timer = 0  # 追尾開始までのタイマー
        
    def update(self):
        """
        パワーアップアイテムの状態を更新します。
        
        @returns {boolean} - アイテムが画面外に出たらTrue
        """
        # 一定時間経過後に自機追尾を開始
        self.homing_timer += 1
        if self.homing_timer > 180 and not self.is_homing:  # 3秒後
            self.is_homing = True
            
        # 自機追尾モード
        if self.is_homing:
            # 激しく揺れながら高速で下に落ちる
            self.speed = self.base_speed * 3
            self.x += math.sin(pyxel.frame_count / 5 + self.sin_offset) * 1.5
        else:
            # 通常の動き
            self.hover_time += 1
            # ゆっくりと下に落ち、左右に少し揺れる
            self.y += self.speed
            self.x += math.sin(pyxel.frame_count / 15 + self.sin_offset) * 0.5
        
        # 画面外に出たら削除
        if self.x < -self.width or self.x > pyxel.width + self.width or self.y > pyxel.height + self.height:
            return True
        return False
        
    def draw(self):
        """
        パワーアップアイテムを描画します。
        """
        # アイテムの種類に応じた描画
        if self.item_type == POWER_UP_TYPE_POWER:
            # パワーアップ（P）: 黄色の四角
            pyxel.rect(self.x, self.y, self.width, self.height, 14)  # 黄色
            pyxel.text(self.x + 2, self.y + 2, "P", 0)
        elif self.item_type == POWER_UP_TYPE_LIFE:
            # 残機アップ（L）: 赤い四角
            pyxel.rect(self.x, self.y, self.width, self.height, 8)  # 赤色
            pyxel.text(self.x + 2, self.y + 2, "L", 7)
        elif self.item_type == POWER_UP_TYPE_BOMB:
            # ボムアップ（B）: 青い四角
            pyxel.rect(self.x, self.y, self.width, self.height, 12)  # 青色
            pyxel.text(self.x + 2, self.y + 2, "B", 7)
            
        # 点滅エフェクト（特に自機追尾モード時）
        if self.is_homing and pyxel.frame_count % 4 < 2:
            # 反転色で縁取り
            col = 7 if pyxel.frame_count % 8 < 4 else 10
            pyxel.rectb(self.x - 1, self.y - 1, self.width + 2, self.height + 2, col)
            
    def apply_effect(self, player):
        """
        プレイヤーにアイテム効果を適用します。
        
        @param {Player} player - 効果を適用するプレイヤーオブジェクト
        @returns {number} - 獲得したスコア
        """
        if self.item_type == POWER_UP_TYPE_POWER:
            player.power_up()
            return 50  # パワーアップの点数
        elif self.item_type == POWER_UP_TYPE_LIFE:
            player.add_life()
            return 200  # 残機アップの点数
        elif self.item_type == POWER_UP_TYPE_BOMB:
            player.add_bomb()
            return 100  # ボムアップの点数
        return 0 