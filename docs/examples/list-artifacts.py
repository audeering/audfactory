import audfactory


pom_url = audfactory.server_pom_url(
    'com.audeering.data.timit', 'timit', '1.1.0',
)
pom = audfactory.download_pom(pom_url)
deps = audfactory.transitive_dependencies(pom)
urls = audfactory.list_artifacts(deps)
print(urls)
