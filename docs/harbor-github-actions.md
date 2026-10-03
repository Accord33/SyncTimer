# GitHub Actions → Tailscale → Harbor: 再利用用テンプレート

## 目的

GitHub Actions の一時RunnerからTailscale経由で自宅Harborへ接続し、Dockerイメージをコミット単位の不変タグでpushする再利用workflowと、コピー用テンプレートの手順です。

このリポジトリで確認済みの経路は次です。

```text
GitHub Actions Runner
  └─ Tailscale (tag:ci)
       └─ Harbor: harbor.accordlab
            └─ <HARBOR_PROJECT>/<IMAGE_NAME>:sha-<commit SHA>
```

Kubernetesへの反映はこのテンプレートの責務に含めません。イメージpushの成功を独立して確認してから、別のデプロイ手順で利用します。

## コピーして単体利用する場合

別リポジトリから共通workflowを呼び出す方法は、後述の「他リポジトリから利用する」を参照してください。対象リポジトリへworkflow一式をコピーし、そのリポジトリで独立管理したい場合は、以下を使います。

1. 対象リポジトリへ [`templates/github-actions/publish-harbor-image.yml`](../templates/github-actions/publish-harbor-image.yml) を `.github/workflows/publish-harbor-image.yml` としてコピーします。
2. 次の値を対象プロジェクト用に置換します。

   ```yaml
   HARBOR_IMAGE: harbor.accordlab/<HARBOR_PROJECT>/<IMAGE_NAME>
   ```

   例：SyncTimerでは `harbor.accordlab/synctimer/synctimer` です。

3. `test` ジョブの `Verify container build input` を、対象プロジェクトの実テストへ置換します。例：

   ```yaml
   - name: Run tests
     run: pytest -q
   ```

4. GitHub Secretsを設定し、まず `workflow_dispatch` で1回実行します。
5. ログの `Published image:` が期待する `sha-<commit SHA>` タグを示すことを確認します。

## 他リポジトリから利用する

`.github/workflows/reusable-harbor-publish.yml` は GitHub Actions の `workflow_call` 再利用ワークフローです。対象リポジトリへコピーせず、SyncTimer リポジトリから直接呼び出せます。SyncTimerリポジトリは公開設定です。GitHubでは公開workflowは公開／非公開いずれの呼び出し元からも利用できますが、公開リポジトリの呼び出し元は公開workflowのみ利用可能です。呼び出し元リポジトリのActionsポリシーで公開workflowが制限されている場合は、`Accord33/SyncTimer` を許可してください。詳細はGitHub公式の[再利用workflow説明](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)と[リポジトリ設定](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository)を参照してください。

呼び出し元リポジトリの `.github/workflows/build-and-publish.yml` に、次のjobを追加します。PRが `main` にマージされた後は、まず `@main` を指定して利用できます。安定運用では、確認済みの完全なcommit SHAへ固定してください。

```yaml
jobs:
  test:
    # 呼び出し元プロジェクト自身のテストをここで実行
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./run-tests.sh

  publish:
    needs: test
    uses: Accord33/SyncTimer/.github/workflows/reusable-harbor-publish.yml@main
    with:
      harbor_host: harbor.accordlab
      image_repository: my-project/my-image
      tailscale_tags: tag:ci
      platform: linux/amd64
    secrets:
      TAILSCALE_OAUTH_CLIENT_ID: ${{ secrets.TAILSCALE_OAUTH_CLIENT_ID }}
      TAILSCALE_OAUTH_CLIENT_SECRET: ${{ secrets.TAILSCALE_OAUTH_CLIENT_SECRET }}
      HARBOR_IP: ${{ secrets.HARBOR_IP }}
      HARBOR_USERNAME: ${{ secrets.HARBOR_USERNAME }}
      HARBOR_PASSWORD: ${{ secrets.HARBOR_PASSWORD }}
```

呼び出し元で必要な準備：

1. GitHub Actions の設定で、公開リポジトリのActions／再利用workflowを許可する（Organizationのポリシーが優先される場合があります）。
2. 呼び出し元リポジトリのActions secrets、またはそのリポジトリに公開したOrganization secretsへ、表記の5つのSecretsを登録する。
3. `harbor_host` と `image_repository` を指定する。`image_repository` は `<Harbor project>/<image name>` 形式であり、Harborプロジェクトを先に作成してCIロボットアカウントへpush権限を付ける。
4. 呼び出し元リポジトリのルートに `Dockerfile` を置く。再利用workflowは呼び出し元リポジトリをcheckoutし、そのルートをDocker build contextとして使う。

イメージタグの `github.sha` は呼び出し元のcommit SHAです。公開先は `<harbor_host>/<image_repository>:sha-<呼び出し元commit SHA>` になります。

## 前提条件

### Harbor

- `HARBOR_PROJECT` に対応するプロジェクトがHarbor上に作成済みであること。
- CI用ロボットアカウントに当該プロジェクトのpush権限があること。
- `harbor.accordlab` がTailscale接続後に到達可能であること。
- 現行Harborは自己署名証明書を使うため、テンプレートはRunnerのDocker daemonへ `insecure-registries` を設定します。

### Tailscale

- GitHub Actions用OAuthクライアントが作成済みであること。
- OAuthクライアントが `tag:ci` を付与できること。
- ACLで `tag:ci` からHarborへの到達を許可していること。

## GitHub Secrets

対象リポジトリの **Settings → Secrets and variables → Actions** に、次をRepository secretとして設定します。

| Secret | 用途 |
| --- | --- |
| `TAILSCALE_OAUTH_CLIENT_ID` | GitHub Actions用Tailscale OAuthクライアントID |
| `TAILSCALE_OAUTH_CLIENT_SECRET` | GitHub Actions用Tailscale OAuthシークレット |
| `HARBOR_IP` | Actions Runnerが`harbor.accordlab`として到達するHarborのTailscale IP |
| `HARBOR_USERNAME` | Harborロボットアカウント名 |
| `HARBOR_PASSWORD` | Harborロボットアカウントトークン |

認証情報はリポジトリへ書かず、Secretsだけに保持します。Harborロボットアカウント名には `$` を含むことがあるため、テンプレートの `HARBOR_USERNAME` / `HARBOR_PASSWORD` の環境変数経由と `printf '%s'` のログイン形式を変更しないでください。

## テンプレートの動作

`templates/github-actions/publish-harbor-image.yml` は次を行います。

1. `main` へのpush、または手動実行で起動。
2. 先に対象プロジェクトのテストを実行。
3. Tailscaleへ `tag:ci` として接続。
4. `HARBOR_IP` を一時的に `harbor.accordlab` へ解決させる。
5. Harborへログイン。
6. `sha-${{ github.sha }}` タグでLinux/amd64イメージをビルドし、Harborへpush。

`latest` は使用しません。デプロイ側では、CIログに出た完全な不変タグを参照します。

## 実行確認

GitHub Actionsの対象Runで、以下がすべて成功していることを確認します。

- `Test`
- `Connect to Tailscale`
- `Login to Harbor`
- `Build and push immutable image`

最後のログ例：

```text
Published image: harbor.accordlab/synctimer/synctimer:sha-31f5f49bebbfaea02440e59c58eb2537ba28df12
```

## 失敗時の切り分け

### `unauthorized: project <name> not found`

Harborプロジェクト名が違う、プロジェクトが未作成、またはロボットアカウントに対象プロジェクトの権限がありません。`HARBOR_IMAGE` のプロジェクト部分とHarborのプロジェクト名を一致させます。

### `docker login` が失敗する

`HARBOR_USERNAME` / `HARBOR_PASSWORD`、Harborのロボットアカウント状態、または`HARBOR_IP`とTailscale ACLを確認します。ユーザー名・パスワードをワークフロー本文へ直接埋め込んではいけません。

### 証明書エラー

現行構成では `insecure-registries` を設定するテンプレートを使います。Harborの正規証明書をRunnerが信頼できる構成へ移行した場合は、この設定を削除し、Dockerの通常TLS検証へ切り替えます。

## SyncTimerでの検証済み値

- Harborプロジェクト：`synctimer`
- イメージ名：`synctimer`
- 正しいイメージ参照：`harbor.accordlab/synctimer/synctimer`
- 初回の成功タグ：`sha-31f5f49bebbfaea02440e59c58eb2537ba28df12`
