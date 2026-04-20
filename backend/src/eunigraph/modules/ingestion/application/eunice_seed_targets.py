from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EUNICETargetOrganizationSpec:
    key: str
    display_name: str
    aliases: tuple[str, ...]
    country_code: str | None = None


DEFAULT_EUNICE_TARGET_ORGANIZATIONS: tuple[EUNICETargetOrganizationSpec, ...] = (
    EUNICETargetOrganizationSpec(
        key="unict",
        display_name="Universita di Catania",
        aliases=(
            "Universita di Catania",
            "Università di Catania",
            "University of Catania",
            "UNICT",
        ),
        country_code="IT",
    ),
    EUNICETargetOrganizationSpec(
        key="btu",
        display_name="Brandenburg University of Technology Cottbus-Senftenberg",
        aliases=(
            "Brandenburg University of Technology",
            "Brandenburg University of Technology Cottbus-Senftenberg",
            "BTU",
            "BUT",
        ),
        country_code="DE",
    ),
    EUNICETargetOrganizationSpec(
        key="cantabria",
        display_name="Universidad de Cantabria",
        aliases=(
            "Universidad de Cantabria",
            "University of Cantabria",
            "Universita di Cantabria",
            "Università di Cantabria",
        ),
        country_code="ES",
    ),
    EUNICETargetOrganizationSpec(
        key="umons",
        display_name="Universite de Mons",
        aliases=(
            "Universite de Mons",
            "Université de Mons",
            "University of Mons",
            "Universita di Mons",
            "Università di Mons",
            "UMONS",
        ),
        country_code="BE",
    ),
    EUNICETargetOrganizationSpec(
        key="peloponnese",
        display_name="University of the Peloponnese",
        aliases=(
            "University of the Peloponnese",
            "University of Peloponnese",
            "Universita del Peloponneso",
            "Università del Peloponneso",
            "Panepistimio Peloponnisou",
            "Πανεπιστήμιο Πελοποννήσου",
        ),
        country_code="GR",
    ),
    EUNICETargetOrganizationSpec(
        key="poznan-tech",
        display_name="Poznan University of Technology",
        aliases=(
            "Poznan University of Technology",
            "Poznan University of Technology PUT",
            "Politechnika Poznanska",
            "Politechnika Poznańska",
        ),
        country_code="PL",
    ),
    EUNICETargetOrganizationSpec(
        key="vaasa",
        display_name="University of Vaasa",
        aliases=(
            "University of Vaasa",
            "Universita di Vaasa",
            "Università di Vaasa",
        ),
        country_code="FI",
    ),
    EUNICETargetOrganizationSpec(
        key="viseu",
        display_name="Instituto Politecnico de Viseu",
        aliases=(
            "Instituto Politecnico de Viseu",
            "Instituto Politécnico de Viseu",
            "Polytechnic Institute of Viseu",
            "Istituto Politecnico di Viseu",
            "IPV",
        ),
        country_code="PT",
    ),
    EUNICETargetOrganizationSpec(
        key="mub",
        display_name="Medical University of Bialystok",
        aliases=(
            "Medical University of Bialystok",
            "Medical University of Bialystok in Poland",
            "Uniwersytet Medyczny w Bialymstoku",
            "Uniwersytet Medyczny w Białymstoku",
        ),
        country_code="PL",
    ),
)
