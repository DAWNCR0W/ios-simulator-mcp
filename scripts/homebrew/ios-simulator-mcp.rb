class IosSimulatorMcp < Formula
  include Language::Python::Virtualenv

  desc "MCP server for controlling iOS Simulator via macOS Accessibility APIs"
  homepage "https://github.com/DAWNCR0W/ios-simulator-mcp"
  url "https://github.com/DAWNCR0W/ios-simulator-mcp/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "<sha256>"
  license "MIT"

  depends_on "python@3.11"

  # Populate resources with `brew update-python-resources Formula/ios-simulator-mcp.rb`.
  # resource "mcp" do
  #   url "https://files.pythonhosted.org/packages/.../mcp-1.25.0.tar.gz"
  #   sha256 "<sha256>"
  # end
  #
  # resource "pyobjc" do
  #   url "https://files.pythonhosted.org/packages/.../pyobjc-12.1.tar.gz"
  #   sha256 "<sha256>"
  # end

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/ios-simulator-mcp", "--help"
  end
end
