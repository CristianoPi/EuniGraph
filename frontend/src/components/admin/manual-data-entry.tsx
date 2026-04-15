"use client";

import Link from "next/link";
import type { Route } from "next";
import type { ReactNode } from "react";
import { useForm } from "react-hook-form";

import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { Panel } from "@/components/ui/panel";
import {
  useCreateOrganizationMutation,
  useCreatePublicationMutation,
  useCreateResearcherMutation,
} from "@/hooks/use-admin";
import { ApiError } from "@/lib/api/client";

const inputClass =
  "rounded-[1.25rem] border border-[color:var(--border)] bg-white/80 px-4 py-3 text-sm outline-none focus:border-pine";
const textareaClass = `${inputClass} min-h-32 resize-y`;
const buttonClass = "rounded-full bg-pine px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50";

type PublicationFormValues = {
  title: string;
  abstract: string;
  publication_year: string;
  publication_date: string;
  doi: string;
  openaire_id: string;
  publication_type: string;
  language_code: string;
  journal_name: string;
  venue_name: string;
  publisher: string;
  open_access: "unset" | "true" | "false";
  source_url: string;
};

type ResearcherFormValues = {
  full_name: string;
  given_name: string;
  family_name: string;
  display_name: string;
  orcid: string;
  email: string;
  profile_url: string;
  primary_organization_id: string;
};

type OrganizationFormValues = {
  name: string;
  organization_type: string;
  country_code: string;
  city: string;
  website: string;
  parent_organization_id: string;
  ror_id: string;
  openaire_id: string;
};

function optionalText(value: string): string | null {
  const normalized = value.trim();
  return normalized || null;
}

function optionalNumber(value: string): number | null {
  const normalized = value.trim();
  return normalized ? Number(normalized) : null;
}

function optionalBoolean(value: PublicationFormValues["open_access"]): boolean | null {
  if (value === "true") {
    return true;
  }

  if (value === "false") {
    return false;
  }

  return null;
}

function formatError(error: unknown): string {
  if (error instanceof ApiError) {
    if (typeof error.detail === "string") {
      return error.detail;
    }

    return JSON.stringify(error.detail);
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unexpected error while creating the canonical entity.";
}

function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: ReactNode;
  hint?: string;
}) {
  return (
    <label className="space-y-2">
      <span className="block text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
        {label}
      </span>
      {children}
      {hint ? <span className="block text-xs leading-5 text-slate-500">{hint}</span> : null}
    </label>
  );
}

function CreateFeedback({
  isPending,
  isSuccess,
  isError,
  error,
  success,
  href,
}: {
  isPending: boolean;
  isSuccess: boolean;
  isError: boolean;
  error: unknown;
  success: string;
  href?: Route;
}) {
  if (isPending) {
    return <LoadingState label="Creating canonical entity..." />;
  }

  if (isError) {
    return <ErrorState title="Create request failed" message={formatError(error)} />;
  }

  if (isSuccess) {
    return (
      <div className="rounded-3xl border border-pine/20 bg-pine/10 p-5 text-sm leading-6 text-slate-700">
        <p className="font-semibold text-pine">{success}</p>
        {href ? (
          <Link href={href} className="mt-3 inline-flex font-semibold text-pine underline">
            Open detail view
          </Link>
        ) : null}
      </div>
    );
  }

  return null;
}

function publicationRoute(id: string): Route {
  return `/entities/publications/${id}` as Route;
}

function researcherRoute(id: string): Route {
  return `/entities/researchers/${id}` as Route;
}

function organizationRoute(id: string): Route {
  return `/entities/organizations/${id}` as Route;
}

function PublicationForm() {
  const mutation = useCreatePublicationMutation();
  const { handleSubmit, register, reset } = useForm<PublicationFormValues>({
    defaultValues: {
      title: "",
      abstract: "",
      publication_year: "",
      publication_date: "",
      doi: "",
      openaire_id: "",
      publication_type: "",
      language_code: "",
      journal_name: "",
      venue_name: "",
      publisher: "",
      open_access: "unset",
      source_url: "",
    },
  });

  return (
    <Panel
      title="Create Publication"
      description="Create one canonical publication through the existing manual entity API."
    >
      <form
        onSubmit={handleSubmit((values) =>
          mutation.mutate(
            {
              title: values.title.trim(),
              abstract: optionalText(values.abstract),
              publication_year: optionalNumber(values.publication_year),
              publication_date: optionalText(values.publication_date),
              doi: optionalText(values.doi),
              openaire_id: optionalText(values.openaire_id),
              publication_type: optionalText(values.publication_type),
              language_code: optionalText(values.language_code),
              journal_name: optionalText(values.journal_name),
              venue_name: optionalText(values.venue_name),
              publisher: optionalText(values.publisher),
              open_access: optionalBoolean(values.open_access),
              source_url: optionalText(values.source_url),
            },
            { onSuccess: () => reset() },
          ),
        )}
        className="space-y-5"
      >
        <Field label="Title">
          <input
            {...register("title", { required: true })}
            className={inputClass}
            placeholder="Publication title"
          />
        </Field>
        <Field label="Abstract">
          <textarea {...register("abstract")} className={textareaClass} placeholder="Optional abstract" />
        </Field>
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Publication year">
            <input
              {...register("publication_year")}
              className={inputClass}
              inputMode="numeric"
              placeholder="2026"
            />
          </Field>
          <Field label="Publication date">
            <input {...register("publication_date")} className={inputClass} type="date" />
          </Field>
          <Field label="DOI">
            <input {...register("doi")} className={inputClass} placeholder="10.xxxx/example" />
          </Field>
          <Field label="OpenAIRE ID">
            <input {...register("openaire_id")} className={inputClass} placeholder="Optional source id" />
          </Field>
          <Field label="Publication type">
            <input {...register("publication_type")} className={inputClass} placeholder="article" />
          </Field>
          <Field label="Language code">
            <input {...register("language_code")} className={inputClass} placeholder="en" />
          </Field>
          <Field label="Journal name">
            <input {...register("journal_name")} className={inputClass} placeholder="Optional journal" />
          </Field>
          <Field label="Venue name">
            <input {...register("venue_name")} className={inputClass} placeholder="Optional venue" />
          </Field>
          <Field label="Publisher">
            <input {...register("publisher")} className={inputClass} placeholder="Optional publisher" />
          </Field>
          <Field label="Open access">
            <select {...register("open_access")} className={inputClass}>
              <option value="unset">Unknown</option>
              <option value="true">Open access</option>
              <option value="false">Not open access</option>
            </select>
          </Field>
        </div>
        <Field label="Source URL">
          <input {...register("source_url")} className={inputClass} placeholder="Optional canonical URL" />
        </Field>
        <button type="submit" disabled={mutation.isPending} className={buttonClass}>
          Create publication
        </button>
      </form>

      <div className="mt-5">
        <CreateFeedback
          isPending={mutation.isPending}
          isSuccess={mutation.isSuccess}
          isError={mutation.isError}
          error={mutation.error}
          success={`Publication created${mutation.data ? `: ${mutation.data.title}` : "."}`}
          href={mutation.data ? publicationRoute(mutation.data.id) : undefined}
        />
      </div>
    </Panel>
  );
}

function ResearcherForm() {
  const mutation = useCreateResearcherMutation();
  const { handleSubmit, register, reset } = useForm<ResearcherFormValues>({
    defaultValues: {
      full_name: "",
      given_name: "",
      family_name: "",
      display_name: "",
      orcid: "",
      email: "",
      profile_url: "",
      primary_organization_id: "",
    },
  });

  return (
    <Panel
      title="Create Researcher"
      description="Create one canonical researcher. Affiliation links can be added in a later UI iteration."
    >
      <form
        onSubmit={handleSubmit((values) =>
          mutation.mutate(
            {
              full_name: values.full_name.trim(),
              given_name: optionalText(values.given_name),
              family_name: optionalText(values.family_name),
              display_name: optionalText(values.display_name),
              orcid: optionalText(values.orcid),
              email: optionalText(values.email),
              profile_url: optionalText(values.profile_url),
              primary_organization_id: optionalText(values.primary_organization_id),
            },
            { onSuccess: () => reset() },
          ),
        )}
        className="space-y-5"
      >
        <Field label="Full name">
          <input
            {...register("full_name", { required: true })}
            className={inputClass}
            placeholder="Researcher full name"
          />
        </Field>
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Given name">
            <input {...register("given_name")} className={inputClass} placeholder="Optional given name" />
          </Field>
          <Field label="Family name">
            <input {...register("family_name")} className={inputClass} placeholder="Optional family name" />
          </Field>
          <Field label="Display name">
            <input {...register("display_name")} className={inputClass} placeholder="Optional display name" />
          </Field>
          <Field label="ORCID">
            <input {...register("orcid")} className={inputClass} placeholder="0000-0000-0000-0000" />
          </Field>
          <Field label="Email">
            <input {...register("email")} className={inputClass} type="email" placeholder="Optional email" />
          </Field>
          <Field label="Profile URL">
            <input {...register("profile_url")} className={inputClass} placeholder="Optional profile URL" />
          </Field>
        </div>
        <Field
          label="Primary organization ID"
          hint="Optional UUID. The backend validates referential integrity."
        >
          <input
            {...register("primary_organization_id")}
            className={inputClass}
            placeholder="Optional organization UUID"
          />
        </Field>
        <button type="submit" disabled={mutation.isPending} className={buttonClass}>
          Create researcher
        </button>
      </form>

      <div className="mt-5">
        <CreateFeedback
          isPending={mutation.isPending}
          isSuccess={mutation.isSuccess}
          isError={mutation.isError}
          error={mutation.error}
          success={`Researcher created${mutation.data ? `: ${mutation.data.full_name}` : "."}`}
          href={mutation.data ? researcherRoute(mutation.data.id) : undefined}
        />
      </div>
    </Panel>
  );
}

function OrganizationForm() {
  const mutation = useCreateOrganizationMutation();
  const { handleSubmit, register, reset } = useForm<OrganizationFormValues>({
    defaultValues: {
      name: "",
      organization_type: "",
      country_code: "",
      city: "",
      website: "",
      parent_organization_id: "",
      ror_id: "",
      openaire_id: "",
    },
  });

  return (
    <Panel
      title="Create Organization"
      description="Create one canonical organization such as a university, department or institute."
    >
      <form
        onSubmit={handleSubmit((values) =>
          mutation.mutate(
            {
              name: values.name.trim(),
              organization_type: optionalText(values.organization_type),
              country_code: optionalText(values.country_code),
              city: optionalText(values.city),
              website: optionalText(values.website),
              parent_organization_id: optionalText(values.parent_organization_id),
              ror_id: optionalText(values.ror_id),
              openaire_id: optionalText(values.openaire_id),
            },
            { onSuccess: () => reset() },
          ),
        )}
        className="space-y-5"
      >
        <Field label="Name">
          <input
            {...register("name", { required: true })}
            className={inputClass}
            placeholder="Organization name"
          />
        </Field>
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Organization type">
            <input {...register("organization_type")} className={inputClass} placeholder="university" />
          </Field>
          <Field label="Country code">
            <input {...register("country_code")} className={inputClass} placeholder="IT" maxLength={2} />
          </Field>
          <Field label="City">
            <input {...register("city")} className={inputClass} placeholder="Optional city" />
          </Field>
          <Field label="Website">
            <input {...register("website")} className={inputClass} placeholder="Optional website" />
          </Field>
          <Field label="ROR ID">
            <input {...register("ror_id")} className={inputClass} placeholder="Optional ROR id" />
          </Field>
          <Field label="OpenAIRE ID">
            <input {...register("openaire_id")} className={inputClass} placeholder="Optional OpenAIRE id" />
          </Field>
        </div>
        <Field label="Parent organization ID" hint="Optional UUID for department or unit hierarchy.">
          <input
            {...register("parent_organization_id")}
            className={inputClass}
            placeholder="Optional parent organization UUID"
          />
        </Field>
        <button type="submit" disabled={mutation.isPending} className={buttonClass}>
          Create organization
        </button>
      </form>

      <div className="mt-5">
        <CreateFeedback
          isPending={mutation.isPending}
          isSuccess={mutation.isSuccess}
          isError={mutation.isError}
          error={mutation.error}
          success={`Organization created${mutation.data ? `: ${mutation.data.name}` : "."}`}
          href={mutation.data ? organizationRoute(mutation.data.id) : undefined}
        />
      </div>
    </Panel>
  );
}

export function ManualDataEntry() {
  return (
    <div className="grid gap-6">
      <PublicationForm />
      <ResearcherForm />
      <OrganizationForm />
    </div>
  );
}
