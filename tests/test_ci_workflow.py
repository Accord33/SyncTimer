from pathlib import Path


ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "publish-image.yml"
REUSABLE = ROOT / ".github" / "workflows" / "reusable-harbor-publish.yml"
TEMPLATE = ROOT / "templates" / "github-actions" / "publish-harbor-image.yml"
DOC = ROOT / "docs" / "harbor-github-actions.md"


def test_project_workflow_runs_tests_before_calling_reusable_publisher():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "- main" in workflow
    assert "pytest -q" in workflow
    assert "needs: test" in workflow
    assert "uses: ./.github/workflows/reusable-harbor-publish.yml" in workflow
    assert "harbor.accordlab" in workflow
    assert "synctimer/synctimer" in workflow


def test_reusable_workflow_accepts_configuration_and_pushes_immutable_sha_tag():
    workflow = REUSABLE.read_text(encoding="utf-8")
    assert "workflow_call:" in workflow
    assert "harbor_host:" in workflow
    assert "image_repository:" in workflow
    assert "HARBOR_IP:" in workflow
    assert "TAILSCALE_OAUTH_CLIENT_ID:" in workflow
    assert "HARBOR_USERNAME:" in workflow
    assert "HARBOR_PASSWORD:" in workflow
    assert "sha-${{ github.sha }}" in workflow
    assert 'docker push "$IMAGE:$IMAGE_TAG"' in workflow


def test_reusable_workflow_uses_tailscale_and_safe_docker_login():
    workflow = REUSABLE.read_text(encoding="utf-8")
    assert "tailscale/github-action@v2" in workflow
    assert "tags: ${{ inputs.tailscale_tags }}" in workflow
    assert "insecure-registries" in workflow
    assert 'printf \'%s\' "$HARBOR_PASSWORD"' in workflow
    assert '"$HARBOR_USERNAME"' in workflow


def test_copyable_template_keeps_verified_connection_and_tagging_pattern():
    template = TEMPLATE.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in template
    assert "tailscale/github-action@v2" in template
    assert "tags: tag:ci" in template
    assert "HARBOR_IP" in template
    assert "HARBOR_USERNAME" in template
    assert "HARBOR_PASSWORD" in template
    assert "printf '%s' \"$HARBOR_PASSWORD\"" in template
    assert "HARBOR_IMAGE: harbor.accordlab/<HARBOR_PROJECT>/<IMAGE_NAME>" in template
    assert "sha-${{ github.sha }}" in template
    assert 'docker push "${HARBOR_IMAGE}:${IMAGE_TAG}"' in template
    assert ":latest" not in template


def test_documentation_explains_copy_and_reusable_workflow_patterns():
    documentation = DOC.read_text(encoding="utf-8")
    assert "templates/github-actions/publish-harbor-image.yml" in documentation
    assert ".github/workflows/reusable-harbor-publish.yml" in documentation
    assert "workflow_call" in documentation
    assert "HARBOR_IP" in documentation
    assert "HARBOR_USERNAME" in documentation
    assert "HARBOR_PASSWORD" in documentation
    assert "TAILSCALE_OAUTH_CLIENT_ID" in documentation
    assert "TAILSCALE_OAUTH_CLIENT_SECRET" in documentation
    assert "harbor.accordlab/<HARBOR_PROJECT>/<IMAGE_NAME>" in documentation
    assert "sha-<commit SHA>" in documentation
