"""
東方風弾幕シューティングゲーム

このプログラムはPyxelライブラリを使用した東方プロジェクト風の弾幕シューティングゲームです。
プレイヤーはキャラクターを操作して、さまざまなパターンの弾幕を放つボスと戦います。

特徴:
- 複数の弾幕パターン
- 3段階のボスフェーズ
- パワーアップシステム
- 障害物の回避
- ライフシステム

操作方法:
- 矢印キー: 移動
- Zキー: ショット
- Rキー: リスタート（ゲームオーバー/クリア時）
- Qキー: 終了

作者: [あなたの名前]
バージョン: 1.0.0
"""

import pyxel
import math
import random
from entities.player import Player
from entities.boss import Boss
from entities.obstacle import Obstacle
from entities.power_up import PowerUp
from utils.collision import check_collision
from utils.resource_loader import load_resources

# ゲームの定数
SCREEN_WIDTH = 240
SCREEN_HEIGHT = 320
GAME_TITLE = "東方風弾幕ゲーム"

class Game:
    """
    ゲームのメインクラス
    
    ゲームの初期化、更新、描画、イベント処理などの中心的な機能を担当します。
    """
    def __init__(self):
        """
        ゲームを初期化します。
        
        画面サイズの設定、リソースの読み込み、ゲームの初期状態の設定を行います。
        """
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title=GAME_TITLE)
        
        # リソースの読み込み
        load_resources()
        
        self.reset_game()
        pyxel.run(self.update, self.draw)

    def reset_game(self):
        """
        ゲームをリセットし、初期状態に戻します。
        """
        self.player = Player()
        self.boss = Boss()
        self.obstacles = []
        self.power_ups = []
        self.effects = []  # エフェクト用のリスト
        self.game_over = False
        self.cleared = False
        self.score = 0
        self.frame_counter = 0
        self.stage = 1  # 現在のステージ
        self.game_state = "title"  # ゲームの状態（title, playing, gameover, cleared）

    def update(self):
        """
        ゲームの状態を更新します。
        
        キー入力の処理、オブジェクトの更新、衝突判定などを行います。
        """
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
            
        # ゲームの状態に応じた更新処理
        if self.game_state == "title":
            self.update_title()
        elif self.game_state == "playing":
            self.update_playing()
        elif self.game_state == "gameover" or self.game_state == "cleared":
            if pyxel.btnp(pyxel.KEY_R) or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                self.reset_game()

    def update_title(self):
        """
        タイトル画面の更新処理を行います。
        """
        # Zキーまたは画面タップでゲーム開始
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.game_state = "playing"

    def update_playing(self):
        """
        ゲームプレイ中の更新処理を行います。
        """
        self.frame_counter += 1
        
        # プレイヤーの更新
        self.player.update()
        
        # ボスの更新
        self.boss.update(self.player)
        
        # 障害物の生成
        self.spawn_obstacles()
            
        # パワーアップアイテムの生成
        self.spawn_power_ups()
            
        # 障害物の更新
        self.update_obstacles()
                
        # パワーアップアイテムの更新
        self.update_power_ups()
                
        # 当たり判定の処理
        self.check_collisions()
        
        # エフェクトの更新
        self.update_effects()

    def spawn_obstacles(self):
        """
        障害物を生成します。
        """
        if random.random() < 0.01 and self.frame_counter > 180:  # ゲーム開始から3秒後
            x = random.randint(0, SCREEN_WIDTH - 20)
            self.obstacles.append(Obstacle(x, -20, 20, 20, 2))

    def spawn_power_ups(self):
        """
        パワーアップアイテムを生成します。
        """
        if random.random() < 0.01:  # パワーアップの出現確率
            x = random.randint(0, SCREEN_WIDTH - 8)
            self.power_ups.append(PowerUp(x, -8))

    def update_obstacles(self):
        """
        障害物を更新します。
        """
        for obstacle in self.obstacles[:]:
            if obstacle.update():
                self.obstacles.remove(obstacle)

    def update_power_ups(self):
        """
        パワーアップアイテムを更新します。
        """
        for power_up in self.power_ups[:]:
            if power_up.update():
                self.power_ups.remove(power_up)

    def update_effects(self):
        """
        エフェクトを更新します。
        """
        for effect in self.effects[:]:
            if effect.update():
                self.effects.remove(effect)

    def check_collisions(self):
        """
        衝突判定を処理します。
        """
        # プレイヤー弾とボスの当たり判定
        for bullet in self.player.bullets[:]:
            if check_collision(bullet, self.boss):
                if self.boss.get_hit():
                    self.cleared = True
                    self.game_state = "cleared"
                self.player.bullets.remove(bullet)
                self.score += 10
                # ヒットエフェクトの追加も実装可能
                
        # プレイヤーと敵弾の当たり判定
        for bullet in self.boss.bullets[:]:
            if check_collision(bullet, self.player):
                if self.player.get_hit():
                    if self.player.lives <= 0:
                        self.game_over = True
                        self.game_state = "gameover"
                self.boss.bullets.remove(bullet)
                # 被弾エフェクトの追加も実装可能
                
        # プレイヤーと障害物の当たり判定
        for obstacle in self.obstacles[:]:
            if check_collision(self.player, obstacle):
                if self.player.get_hit():
                    if self.player.lives <= 0:
                        self.game_over = True
                        self.game_state = "gameover"
                self.obstacles.remove(obstacle)
                
        # プレイヤーとパワーアップアイテムの当たり判定
        for power_up in self.power_ups[:]:
            if check_collision(self.player, power_up):
                self.player.power_up()
                self.power_ups.remove(power_up)
                self.score += 50

    def draw(self):
        """
        ゲームの描画を行います。
        """
        pyxel.cls(0)
        
        # ゲームの状態に応じた描画処理
        if self.game_state == "title":
            self.draw_title()
        elif self.game_state == "playing":
            self.draw_playing()
        elif self.game_state == "gameover":
            self.draw_playing()
            self.draw_game_over()
        elif self.game_state == "cleared":
            self.draw_playing()
            self.draw_cleared()

    def draw_title(self):
        """
        タイトル画面を描画します。
        """
        # 背景の星
        self.draw_stars()
        
        # タイトルテキスト
        pyxel.text(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 3, "東方風弾幕ゲーム", 7)
        
        # 点滅する指示テキスト（Zキーorタップ）
        if pyxel.frame_count % 30 < 15:
            # 背景を追加して目立たせる
            pyxel.rectb(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 5, 160, 15, 11)  # 紫色の枠
            pyxel.text(SCREEN_WIDTH // 2 - 75, SCREEN_HEIGHT // 2, "画面タップまたはZキーでスタート", 10)  # 青色のテキスト
        else:
            pyxel.rectb(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 5, 160, 15, 7)  # 白色の枠
            pyxel.text(SCREEN_WIDTH // 2 - 75, SCREEN_HEIGHT // 2, "画面タップまたはZキーでスタート", 7)  # 白色のテキスト
        
        # 操作説明
        pyxel.text(10, SCREEN_HEIGHT - 120, "操作方法:", 7)
        
        # キーボード操作
        pyxel.text(10, SCREEN_HEIGHT - 110, "【キーボード】", 6)
        pyxel.text(10, SCREEN_HEIGHT - 100, "矢印キー: 移動", 7)
        pyxel.text(10, SCREEN_HEIGHT - 90, "Zキー: ショット", 7)
        pyxel.text(10, SCREEN_HEIGHT - 80, "Xキー: ボム使用", 7)
        pyxel.text(10, SCREEN_HEIGHT - 70, "Rキー: リスタート", 7)
        pyxel.text(10, SCREEN_HEIGHT - 60, "Qキー: 終了", 7)
        
        # タッチ操作
        pyxel.text(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 110, "【タッチ操作】", 6)
        pyxel.text(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100, "画面上部: タップで直接移動", 7)
        pyxel.text(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 90, "画面下部: 高速ジョイスティック", 11)
        pyxel.text(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80, "  • 長押しで徐々に加速", 10)
        pyxel.text(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 70, "  • 大きく動かすと速度アップ", 10)
        pyxel.text(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60, "ダブルタップ: ボム使用", 7)

    def draw_playing(self):
        """
        ゲームプレイ中の描画を行います。
        """
        # 背景の星
        self.draw_stars()
            
        # ゲームオブジェクトの描画
        for obstacle in self.obstacles:
            obstacle.draw()
            
        for power_up in self.power_ups:
            power_up.draw()
            
        for effect in self.effects:
            effect.draw()
            
        self.boss.draw()
        self.player.draw()
        
        # 操作ガイド領域の描画（プレイ開始後5秒間のみ表示）
        if self.frame_counter < 300:  # 5秒 = 60フレーム × 5
            # 操作領域の境界線
            pyxel.line(0, pyxel.height - 200, pyxel.width, pyxel.height - 200, 5)
            
            # 操作ガイド（透明度を徐々に下げる）
            if self.frame_counter < 150:  # 最初の2.5秒は完全表示
                alpha = 255
            else:  # 残りの2.5秒でフェードアウト
                alpha = 255 * (1 - (self.frame_counter - 150) / 150)
                
            alpha_col = int(alpha / 255 * 7)  # 色の透明度を0-7の範囲に変換
            if alpha_col > 0:
                # 上部エリアのガイド
                pyxel.text(5, pyxel.height - 230, "タップで直接移動", alpha_col)
                
                # 下部エリアのガイド
                text_col = min(alpha_col + 3, 7)  # 少し目立つ色に
                pyxel.text(5, pyxel.height - 190, "高速ジョイスティック操作エリア", text_col)
                
                # 新操作方法の説明
                if self.frame_counter % 60 < 30:  # 点滅表示
                    pyxel.text(5, pyxel.height - 180, "• 長押しで徐々に加速", 10)
                    pyxel.text(5, pyxel.height - 170, "• 大きく動かすと速度アップ", 10)
                    pyxel.text(5, pyxel.height - 160, "• ダブルタップでボム使用", 10)
                else:
                    pyxel.text(5, pyxel.height - 180, "• 長押しで徐々に加速", alpha_col)
                    pyxel.text(5, pyxel.height - 170, "• 大きく動かすと速度アップ", alpha_col)
                    pyxel.text(5, pyxel.height - 160, "• ダブルタップでボム使用", alpha_col)
        
        # UI表示
        self.draw_ui()

    def draw_stars(self):
        """
        背景の星を描画します。
        """
        for i in range(50):
            x = (i * 7 + pyxel.frame_count) % SCREEN_WIDTH
            y = (i * 11 + pyxel.frame_count // 2) % SCREEN_HEIGHT
            pyxel.pset(x, y, 6)

    def draw_ui(self):
        """
        UIを描画します。
        """
        pyxel.text(5, SCREEN_HEIGHT - 20, f"スコア:{self.score}", 7)
        pyxel.text(5, SCREEN_HEIGHT - 10, f"残機:{self.player.lives}", 7)
        pyxel.text(SCREEN_WIDTH - 50, SCREEN_HEIGHT - 10, f"パワー:{self.player.power}", 7)

    def draw_game_over(self):
        """
        ゲームオーバー画面を描画します。
        """
        # 背景を暗くする
        pyxel.rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0)
        
        # 画面中央に半透明の黒い背景ボックス
        pyxel.rect(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 60, 160, 120, 1)
        pyxel.rectb(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 60, 160, 120, 8)  # 赤い枠
        
        # ゲームオーバーテキスト
        pyxel.text(SCREEN_WIDTH // 2 - 35, SCREEN_HEIGHT // 2 - 45, "ゲームオーバー", 8)
        
        # 点滅する白い線
        if pyxel.frame_count % 20 < 10:
            pyxel.line(
                SCREEN_WIDTH // 2 - 60, 
                SCREEN_HEIGHT // 2 - 30, 
                SCREEN_WIDTH // 2 + 60, 
                SCREEN_HEIGHT // 2 - 30, 
                7
            )
        
        # ゲーム結果情報
        pyxel.text(SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 - 15, f"最終スコア: {self.score}", 7)
        pyxel.text(SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2, f"残機: 0", 7)
        pyxel.text(SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 + 15, f"パワーレベル: {self.player.power}", 7)
        
        # 再挑戦メッセージ
        if pyxel.frame_count % 30 < 15:
            pyxel.text(SCREEN_WIDTH // 2 - 75, SCREEN_HEIGHT // 2 + 40, "タップまたはRキーでリスタート", 10)
        else:
            pyxel.text(SCREEN_WIDTH // 2 - 75, SCREEN_HEIGHT // 2 + 40, "タップまたはRキーでリスタート", 7)

    def draw_cleared(self):
        """
        クリア画面を描画します。
        """
        # 背景を暗くする（暗めの青色）
        pyxel.rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 1)
        
        # 画面中央に半透明の背景ボックス
        pyxel.rect(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 60, 160, 120, 5)
        pyxel.rectb(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 60, 160, 120, 11)  # 紫色の枠
        
        # クリアテキスト
        pyxel.text(SCREEN_WIDTH // 2 - 40, SCREEN_HEIGHT // 2 - 45, "ステージクリア！", 10)
        
        # 点滅する白い線
        if pyxel.frame_count % 20 < 10:
            pyxel.line(
                SCREEN_WIDTH // 2 - 60, 
                SCREEN_HEIGHT // 2 - 30, 
                SCREEN_WIDTH // 2 + 60, 
                SCREEN_HEIGHT // 2 - 30, 
                7
            )
        
        # ゲーム結果情報
        pyxel.text(SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 - 15, f"最終スコア: {self.score}", 7)
        pyxel.text(SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2, f"残機: {self.player.lives}", 7)
        pyxel.text(SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 + 15, f"パワーレベル: {self.player.power}", 7)
        
        # おめでとうメッセージ
        pyxel.text(SCREEN_WIDTH // 2 - 35, SCREEN_HEIGHT // 2 + 30, "おめでとう！", 10)
        
        # 再挑戦メッセージ
        if pyxel.frame_count % 30 < 15:
            pyxel.text(SCREEN_WIDTH // 2 - 75, SCREEN_HEIGHT // 2 + 45, "タップまたはRキーでリスタート", 11)
        else:
            pyxel.text(SCREEN_WIDTH // 2 - 75, SCREEN_HEIGHT // 2 + 45, "タップまたはRキーでリスタート", 7)

if __name__ == "__main__":
    Game() 