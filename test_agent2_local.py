from agents.material_requirement import (
    MaterialRequirement,
    _retrieve_material_context,
)


def main():
    print("=" * 70)
    print("INFRA MINER AI — AGENT 2 LOCAL VALIDATION")
    print("=" * 70)

    print("\n[1/2] Testing material-context retrieval...")
    context = _retrieve_material_context()

    assert context.strip()
    print("PASS: Material context retrieved from the persistent DPR index.")

    print("\n[2/2] Testing material output schema...")
    sample = MaterialRequirement(
        material_name="Rock Armour",
        quantity=100000.0,
        unit="tonnes",
        specification="Specified rock size",
        purpose="Breakwater",
        alternatives=["Concrete Armour Units"],
    )

    data = sample.model_dump()

    assert data["material_name"] == "Rock Armour"
    assert data["quantity"] == 100000.0
    assert data["unit"] == "tonnes"
    assert isinstance(data["alternatives"], list)

    print("PASS: MaterialRequirement schema is valid.")
    print("\n" + "=" * 70)
    print("AGENT 2 LOCAL VALIDATION PASSED")
    print("=" * 70)
    print("\nNo Gemini API request was made.")


if __name__ == "__main__":
    main()
