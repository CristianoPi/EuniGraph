from __future__ import annotations

from dataclasses import dataclass

from eunigraph.shared.utils import normalize_text


@dataclass(frozen=True, slots=True)
class EUNICEUniversitySpec:
    code: str
    name: str
    color: str
    aliases: tuple[str, ...]
    country_code: str | None = None

    @property
    def normalized_aliases(self) -> tuple[str, ...]:
        return tuple(normalize_text(alias) for alias in self.aliases)


EUNICE_UNIVERSITY_SPECS: tuple[EUNICEUniversitySpec, ...] = (
    EUNICEUniversitySpec(
        code="karlstad",
        name="Karlstad University",
        color="#F4E600",
        aliases=(
            "Karlstad University",
            "Karlstads universitet",
        ),
        country_code="SE",
    ),
    EUNICEUniversitySpec(
        code="vaasa",
        name="University of Vaasa",
        color="#F5C439",
        aliases=(
            "University of Vaasa",
            "Universita di Vaasa",
            "Università di Vaasa",
        ),
        country_code="FI",
    ),
    EUNICEUniversitySpec(
        code="btu",
        name="Brandenburg University of Technology",
        color="#A6C60D",
        aliases=(
            "Brandenburg University of Technology",
            "Brandenburg University of Technology Cottbus-Senftenberg",
            "BTU",
            "BUT",
        ),
        country_code="DE",
    ),
    EUNICEUniversitySpec(
        code="poznan-tech",
        name="Poznan University of Technology",
        color="#00618E",
        aliases=(
            "Poznan University of Technology",
            "Politechnika Poznanska",
            "Politechnika Poznańska",
            "PUT",
        ),
        country_code="PL",
    ),
    EUNICEUniversitySpec(
        code="unict",
        name="University of Catania",
        color="#007DCB",
        aliases=(
            "University of Catania",
            "Universita di Catania",
            "Università di Catania",
            "Universita degli Studi di Catania",
            "UNICT",
        ),
        country_code="IT",
    ),
    EUNICEUniversitySpec(
        code="peloponnese",
        name="University of the Peloponnese",
        color="#A51317",
        aliases=(
            "University of the Peloponnese",
            "Universita del Peloponneso",
            "Università del Peloponneso",
            "Panepistimio Peloponnisou",
        ),
        country_code="GR",
    ),
    EUNICEUniversitySpec(
        code="cantabria",
        name="University of Cantabria",
        color="#438D96",
        aliases=(
            "University of Cantabria",
            "Universidad de Cantabria",
            "Universita di Cantabria",
            "Università di Cantabria",
            "UC",
        ),
        country_code="ES",
    ),
    EUNICEUniversitySpec(
        code="viseu",
        name="Polytechnic Institute of Viseu",
        color="#010101",
        aliases=(
            "Polytechnic Institute of Viseu",
            "Instituto Politecnico de Viseu",
            "Instituto Politécnico de Viseu",
            "Istituto Politecnico di Viseu",
            "IPV",
        ),
        country_code="PT",
    ),
    EUNICEUniversitySpec(
        code="umons",
        name="Université de Mons",
        color="#B60038",
        aliases=(
            "Universite de Mons",
            "Université de Mons",
            "University of Mons",
            "UMONS",
        ),
        country_code="BE",
    ),
    EUNICEUniversitySpec(
        code="uphf",
        name="Université Polytechnique Hauts-de-France",
        color="#46B6C6",
        aliases=(
            "Université Polytechnique Hauts-de-France",
            "Universite Polytechnique Hauts-de-France",
            "University Polytechnic Hauts-de-France",
            "UPHF",
            "Universite de Valenciennes",
            "Université de Valenciennes",
        ),
        country_code="FR",
    ),
)

EUNICE_UNIVERSITY_BY_CODE = {spec.code: spec for spec in EUNICE_UNIVERSITY_SPECS}
