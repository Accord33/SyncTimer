from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "publish-image.yml"


def test_publish_workflow_requires_tests_and_pushes_sha_and_main_latest_tags():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "branches:" in workflow
    assert "- main" in workflow
    assert "needs: test" in workflow
    assert "pytest -q" in workflow
    assert "sha-${{ github.sha }}" in workflow
    assert "docker push \"${HARBOR_IMAGE}:${IMAGE_TAG}\"" in workflow
    assert "HARBOR_IMAGE: harbor.accordlab/synctimer/synctimer" in workflow
    assert '--tag "${HARBOR_IMAGE}:latest"' in workflow
    assert '[[ "$GITHUB_REF" == "refs/heads/main" ]]' in workflow
    assert 'docker push "${HARBOR_IMAGE}:latest"' in workflow


def test_publish_workflow_uses_the_media_server_tailscale_harbor_connection_pattern():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "tailscale/github-action@v2" in workflow
    assert "tags: tag:ci" in workflow
    assert "HARBOR_IP" in workflow
    assert '"insecure-registries": ["harbor.accordlab"]' in workflow
    assert "docker login harbor.accordlab" in workflow
