import copy
import xmltodict


example_pom = xmltodict.parse('''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.audeering.data.database</groupId>
  <artifactId>database</artifactId>
  <version>1.1.3</version>
  <packaging>pom</packaging>
  <description>Test database</description>
  <maintainer>Firstname Lastname</maintainer>
  <url>https://gitlab.audeering.com/data/database</url>
  <licenses>
    <license>
      <name>CC0 1.0</name>
      <url>https://creativecommons.org/publicdomain/zero/1.0/</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>com.audeering.data.database</groupId>
      <artifactId>database-data</artifactId>
      <version>1.0.1</version>
    </dependency>
    <dependency>
      <groupId>com.audeering.data.database</groupId>
      <artifactId>database-metadata</artifactId>
      <version>2.1.0</version>
    </dependency>
  </dependencies>
</project>''')  # noqa: E501

empty_pom = xmltodict.parse('''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <modelVersion>4.0.0</modelVersion>
</project>''')  # noqa: E501

pom_with_empty_deps = copy.deepcopy(example_pom)
pom_with_empty_deps['project']['dependencies'] = None

emodb_pom = xmltodict.parse('''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.audeering.data.emodb</groupId>
  <artifactId>emodb</artifactId>
  <version>0.2.2</version>
  <packaging>pom</packaging>
  <description>Berlin Database of Emotional Speech</description>
  <url>https://gitlab.audeering.com/data/emodb</url>
  <licenses>
    <license>
      <name>CC0 1.0</name>
      <url>https://creativecommons.org/publicdomain/zero/1.0/</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>com.audeering.data.emodb</groupId>
      <artifactId>emodb-data</artifactId>
      <version>0.2.2</version>
    </dependency>
    <dependency>
      <groupId>com.audeering.data.emodb</groupId>
      <artifactId>emodb-metadata</artifactId>
      <version>0.2.2</version>
    </dependency>
  </dependencies>
</project>''')  # noqa: E501
