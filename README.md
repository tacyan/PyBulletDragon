# PyBulletDragon（東方風弾幕シューティングゲーム）

## プロジェクト概要

このプロジェクトは、Pyxelライブラリを使用した東方プロジェクト風の2D弾幕シューティングゲームです。プレイヤーはキャラクターを操作して、様々なパターンの弾幕を放つボスと戦います。

## 主な機能

- 複数の弾幕パターンを持つボス戦
- 3段階のボスフェーズシステム
- パワーアップアイテムシステム
- 障害物の回避要素
- ライフシステム
- 美しい弾幕エフェクト

## 操作方法

- **矢印キー**: 移動
- **Zキー**: ショット発射
- **Rキー**: リスタート（ゲームオーバー/クリア時）
- **Qキー**: ゲーム終了

## インストール方法

1. リポジトリをクローンする
   ```
   git clone https://github.com/tacyan/PyBulletDragon.git
   cd PyBulletDragon
   ```

2. 必要なパッケージをインストールする
   ```
   pip install -r requirements.txt
   ```

## ゲーム起動方法

```
python game.py
```

## プロジェクト構成

- `game.py`: ゲームのメインスクリプト
- `entities/`: ゲーム内のエンティティ（プレイヤー、ボス、障害物など）
  - `player.py`: プレイヤーの実装
  - `boss.py`: ボスの実装
  - `obstacle.py`: 障害物の実装
  - `power_up.py`: パワーアップアイテムの実装
  - `effect.py`: ゲーム内エフェクトの実装
- `utils/`: ユーティリティ関数
  - `collision.py`: 衝突判定処理
  - `resource_loader.py`: リソース読み込み
- `resources/`: ゲームで使用するリソースファイル
  - `game_resources.pyxres`: Pyxelリソースファイル

## 開発環境

- Python 3.6以上
- Pyxel 1.4.3

## ライセンス

このプロジェクトはMITライセンスのもとで公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 謝辞

- このゲームは[東方Project](https://en.touhouwiki.net/wiki/Touhou_Project)からインスピレーションを受けています。
- 開発に[Pyxel](https://github.com/kitao/pyxel)ライブラリを使用しています。 