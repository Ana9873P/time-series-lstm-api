'''
Teste para verificar se a configuração do Datadog está correta.
Verifica se o arquivo docker-compose.yml define um serviço dd-agent e referencia a variável DD_API_KEY.
Também verifica se o README.md menciona Datadog.   

'''



import os


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_docker_compose_exists_and_contains_dd_agent():
    path = os.path.join(os.path.dirname(__file__), "..", "docker-compose.yml")
    path = os.path.abspath(path)
    assert os.path.exists(path), f"Expected {path} to exist"
    content = read(path)
    assert "dd-agent" in content or "dd_agent" in content, "docker-compose.yml should define a dd-agent service"
    assert "DD_API_KEY" in content or "DD_API_KEY=" in content, "docker-compose.yml should reference DD_API_KEY"


def test_readme_mentions_datadog():
    path = os.path.join(os.path.dirname(__file__), "..", "README.md")
    path = os.path.abspath(path)
    assert os.path.exists(path), f"Expected {path} to exist"
    content = read(path).lower()
    assert "datadog" in content, "README.md should mention Datadog"
