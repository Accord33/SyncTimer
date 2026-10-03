from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "publish-image.yml"


def test_publish_workflow_requires_tests_and_pushes_an_immutable_sha_tag():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "branches:" in workflow
    assert "- main" in workflow
    assert "needs: test" in workflow
    assert "pytest -q" in workflow
    assert "sha-${{ github.sha }}" in workflow
    assert "docker push \"${HARBOR_IMAGE}:${IMAGE_TAG}\"" in workflow
    assert "HARBOR_IMAGE: harbor.accordlab/synctimer/synctimer" in workflow
    assert ":latest" not in workflow


def test_publish_workflow_uses_the_media_server_tailscale_harbor_connection_pattern():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "tailscale/github-action@v2" in workflow
    assert "tags: tag:ci" in workflow
    assert "HARBOR_IP" in workflow
    assert '"insecure-registries": ["harbor.accordlab"]' in workflow
    assert "docker login harbor.accordlab" in workflow


def test_harbor_publish_template_keeps_the_verified_connection_and_tagging_pattern():
    template = (
        Path(__file__).parents[1]
        / "templates"
        / "github-actions"
        / "publish-harbor-image.yml"
    ).read_text(encoding="utf-8")

    assert "workflow_dispatch:" in template
    assert "tailscale/github-action@v2" in template
    assert "tags: tag:ci" in template
    assert "HARBOR_IP" in template
    assert "HARBOR_USERNAME" in template
    assert "HARBOR_PASSWORD" in template
    assert "printf '%s' \"$HARBOR_PASSWORD\"" in template
    assert "HARBOR_IMAGE: harbor.accordlab/<HARBOR_PROJECT>/<IMAGE_NAME>" in template
    assert "sha-${{ github.sha }}" in template
    assert "docker push \"${HARBOR_IMAGE}:${IMAGE_TAG}\"" in template
    assert ":latest" not in template


def test_harbor_publish_documentation_lists_reusable_template_and_required_secrets():
    documentation = (
        Path(__file__).parents[1] / "docs" / "harbor-github-actions.md"
    ).read_text(encoding="utf-8")

    assert "templates/github-actions/publish-harbor-image.yml" in documentation
    assert "HARBOR_IP" in documentation
    assert "HARBOR_USERNAME" in documentation
    assert "HARBOR_PASSWORD" in documentation
    assert "TAILSCALE_OAUTH_CLIENT_ID" in documentation
    assert "TAILSCALE_OAUTH_CLIENT_SECRET" in documentation
    assert "harbor.accordlab/<HARBOR_PROJECT>/<IMAGE_NAME>" in documentation
    assert "sha-<commit SHA>" in documentation
