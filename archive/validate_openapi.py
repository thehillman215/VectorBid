#!/usr/bin/env python3
"""
OpenAPI specification validation script for VectorBid API.

This script validates the OpenAPI specification and provides helpful information
about the API endpoints, schemas, and security requirements.
"""

import json
import yaml
import sys
from pathlib import Path


def load_spec(format="yaml"):
    """Load OpenAPI specification from YAML or JSON file."""
    if format == "yaml":
        with open("openapi.yaml", "r") as f:
            return yaml.safe_load(f)
    else:
        with open("openapi.json", "r") as f:
            return json.load(f)


def validate_openapi_structure(spec):
    """Validate basic OpenAPI 3.1 structure."""
    required_fields = ["openapi", "info", "paths"]
    errors = []

    for field in required_fields:
        if field not in spec:
            errors.append(f"Missing required field: {field}")

    # Check OpenAPI version
    if "openapi" in spec:
        version = spec["openapi"]
        if not version.startswith("3.1"):
            errors.append(f"Expected OpenAPI 3.1.x, got: {version}")

    # Check info object
    if "info" in spec:
        info_required = ["title", "version"]
        for field in info_required:
            if field not in spec["info"]:
                errors.append(f"Missing required info field: {field}")

    return errors


def analyze_endpoints(spec):
    """Analyze API endpoints and provide summary."""
    if "paths" not in spec:
        return []

    endpoints = []
    for path, methods in spec["paths"].items():
        for method, details in methods.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                endpoint = {
                    "path": path,
                    "method": method.upper(),
                    "summary": details.get("summary", "No summary"),
                    "security": details.get("security", []),
                    "tags": details.get("tags", []),
                }
                endpoints.append(endpoint)

    return endpoints


def analyze_schemas(spec):
    """Analyze data schemas defined in components."""
    if "components" not in spec or "schemas" not in spec["components"]:
        return []

    schemas = []
    for name, schema in spec["components"]["schemas"].items():
        schema_info = {
            "name": name,
            "type": schema.get("type", "object"),
            "properties": len(schema.get("properties", {})),
            "required": len(schema.get("required", [])),
        }
        schemas.append(schema_info)

    return schemas


def main():
    """Main validation function."""
    print("🔍 VectorBid OpenAPI Specification Validator")
    print("=" * 50)

    # Check if files exist
    yaml_exists = Path("openapi.yaml").exists()
    json_exists = Path("openapi.json").exists()

    if not yaml_exists and not json_exists:
        print("❌ No OpenAPI specification files found!")
        print("Expected: openapi.yaml or openapi.json")
        sys.exit(1)

    # Load specification
    try:
        if yaml_exists:
            spec = load_spec("yaml")
            print("✅ Successfully loaded openapi.yaml")
        else:
            spec = load_spec("json")
            print("✅ Successfully loaded openapi.json")
    except Exception as e:
        print(f"❌ Error loading specification: {e}")
        sys.exit(1)

    # Validate structure
    print("\n📋 Validating OpenAPI structure...")
    errors = validate_openapi_structure(spec)

    if errors:
        print("❌ Validation errors found:")
        for error in errors:
            print(f"  • {error}")
        sys.exit(1)
    else:
        print("✅ OpenAPI structure is valid")

    # Analyze endpoints
    print("\n🛣️  API Endpoints Summary:")
    endpoints = analyze_endpoints(spec)

    if not endpoints:
        print("  No endpoints found")
    else:
        for endpoint in endpoints:
            security_indicator = "🔒" if endpoint["security"] else "🔓"
            tags_str = f" [{', '.join(endpoint['tags'])}]" if endpoint["tags"] else ""
            print(
                f"  {security_indicator} {endpoint['method']} {endpoint['path']}{tags_str}"
            )
            print(f"     {endpoint['summary']}")

    # Analyze schemas
    print("\n📊 Data Schemas Summary:")
    schemas = analyze_schemas(spec)

    if not schemas:
        print("  No schemas found")
    else:
        for schema in schemas:
            print(f"  📄 {schema['name']} ({schema['type']})")
            print(
                f"     Properties: {schema['properties']}, Required: {schema['required']}"
            )

    # Security schemes
    print("\n🔐 Security Schemes:")
    if "components" in spec and "securitySchemes" in spec["components"]:
        for name, scheme in spec["components"]["securitySchemes"].items():
            scheme_type = scheme.get("type", "unknown")
            scheme_scheme = scheme.get("scheme", "")
            print(f"  🔑 {name}: {scheme_type} {scheme_scheme}")
    else:
        print("  No security schemes defined")

    # Summary statistics
    print(f"\n📈 Specification Summary:")
    print(f"  • API Title: {spec['info']['title']}")
    print(f"  • API Version: {spec['info']['version']}")
    print(f"  • OpenAPI Version: {spec['openapi']}")
    print(f"  • Total Endpoints: {len(endpoints)}")
    print(f"  • Total Schemas: {len(schemas)}")
    print(f"  • Servers: {len(spec.get('servers', []))}")

    protected_endpoints = [e for e in endpoints if e["security"]]
    print(f"  • Protected Endpoints: {len(protected_endpoints)}")
    print(f"  • Public Endpoints: {len(endpoints) - len(protected_endpoints)}")

    print("\n✅ OpenAPI specification validation completed successfully!")


if __name__ == "__main__":
    main()
