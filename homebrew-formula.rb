class Mcpverse < Formula
  include Language::Python::Virtualenv

  desc "Command-line interface tool for MCP"
  homepage "https://github.com/mcp/mcpverse-cli"
  url "https://files.pythonhosted.org/packages/source/m/mcpverse/mcpverse-0.1.0.tar.gz"
  sha256 "placeholder_sha256"  # You'll need to update this with the actual SHA once you have a release
  license "MIT"

  depends_on "python@3.8"

  resource "click" do
    url "https://files.pythonhosted.org/packages/43/0e/92b550d04c96b396bcf24bcbf4dd2b338b35037470a8cc3709a37a817c4b/click-8.1.7.tar.gz"
    sha256 "ca9853ad459e787e2192211578cc907e7594e294c7ccc834310722b41b9ca6de"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "URL: https://example.com", shell_output("#{bin}/mcpv proxy https://example.com")
  end
end