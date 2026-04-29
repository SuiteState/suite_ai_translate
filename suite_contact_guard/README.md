# Contact Guard

Phone uniqueness, contact field permissions, and customer activity
status for Odoo 19.

| Available languages |
|---|
| **English** (this file) · [简体中文](README.zh_CN.md) · [العربية](README.ar.md) |

---

## Overview

Contact Guard adds three independent layers of governance to
`res.partner`:

1. ORM-level phone uniqueness, scoped per company
2. Role-based visibility and edit protection on phone, email, and
   salesperson fields
3. Daily-cron customer activity status (Active / Warning / Sleeping
   / Dormant) based on confirmed sale orders

A fourth, supporting feature handles `company_id` defaults so that
single-company users get the same multi-company-safe behaviour that
multi-company users get manually.

All four are configured per company. None of them adds database-
level constraints; enforcement happens at the ORM, field, and view
layers depending on the rule. See [Permissions → Enforcement
layers](#enforcement-layers) for details.

---

## Features

### Phone uniqueness

Phone numbers are normalized to digits-only (stripping `+`, leading
`00`, spaces, dashes, parentheses) and stored in an indexed field
for duplicate detection.

When an internal user creates or edits a contact with a phone
number that already exists in the same company, the operation is
rejected with an error message naming the conflicting number.

The check is bypassed for:

- `env.su` (system automation, migrations, lead-to-contact sync)
- Bulk imports via the standard Import Wizard (`import_file` context)
- Public users (anonymous self-signup visitors)
- Portal users (external customers operating their own data)
- Explicit `suite_skip_phone_check` context flag

The minimum digit length is configurable per company. Default: 8.

### Contact field permissions

Phone, email, and salesperson visibility are gated by role. Once a
contact has an assigned salesperson, their phone and email become
private to that salesperson and to administrators. Contacts without
a salesperson remain visible to all internal users.

The salesperson field is set freely on contact creation (so a user
can claim their own contact, and CRM lead → contact conversion
carries the lead's salesperson over) but locked after creation.

Phone edit protection is enforced at the ORM layer, not just the
view, so it applies to RPC and scripts as well as the web UI.

See **[Permissions](#permissions)** below for the full role-by-role
matrix.

### Customer activity status

When enabled per company, a daily cron computes each customer's
activity status from the date of their last confirmed sale order:

| Status | Condition |
|---|---|
| Active | days since last order < warning threshold |
| Warning | warning <= days < sleeping |
| Sleeping | sleeping <= days < dormant |
| Dormant | days >= dormant |

Customers with no confirmed sale order yet have no status assigned
(blank). Internally this is tracked via a separate `suite_has_orders`
boolean so that "0 days since order" (just placed) and "never
ordered" remain distinguishable, while the days field stays a plain
integer and sorts correctly in list views.

Thresholds are configurable per company. The status appears on the
contact form (Activity Status tab) and the list view (with colour
decoration: yellow for Warning, red for Sleeping, muted grey for
Dormant), and is available for filtering and grouping.

The cron processes customers in batches of 1000 with chatter
notification suppressed.

### Multi-company `company_id` injection

In native Odoo, the `company_id` field on the contact form is
hidden from single-company users, and Odoo defaults it to blank
(meaning the contact is globally visible across companies).

Contact Guard injects the user's active company as the default
`company_id` when creating a contact, so single-company users get
the same per-company scoping that multi-company users can configure
manually.

The injection is suppressed when the contact is being auto-created
as the companion partner of a new `res.company`. In that case,
Odoo's native flow assigns the correct company id, and the
injection would otherwise overwrite it with the *current active*
company's id, breaking downstream routing for the new company.

---

## Configuration

Navigate to:

> **Contacts -> Configuration -> Contact Guard**

(Visible to System Administrators by default.)

**Important:** the protection features are on by default and do not
require a configuration record. Phone uniqueness, field permissions,
and salesperson lock start working the moment the module is installed.
Configuration only lets you tune parameters or opt in to activity
tracking.

| Feature | Default | What configuration changes |
|---|---|---|
| Phone uniqueness | On | Adjusts the minimum digit count (default 8) |
| Field permissions | On | No configuration; behaviour is fixed by role |
| Customer activity status | Off | Enables the daily cron and sets thresholds |

Each company gets its own configuration record:

| Setting | Default | Description |
|---|---|---|
| Phone Min Length | 8 | Minimum digit count after normalization |
| Track Customer Activity | off | Enables the daily activity cron for this company |
| Warning after (days) | 30 | Threshold for Warning status |
| Sleeping after (days) | 60 | Threshold for Sleeping status |
| Dormant after (days) | 90 | Threshold for Dormant status |

Thresholds must satisfy `0 < warning < sleeping < dormant`.

---

## Permissions

### Roles involved

| Role | Group | Source |
|---|---|---|
| Contact Guard Administrator | `suite_contact_guard.group_contact_guard_admin` | Added by this module |
| Sales Manager | `sales_team.group_sale_manager` | Native; **implies** Contact Guard Admin |
| Contact Manager | `base.group_partner_manager` | Native |
| Purchase Manager | `purchase.group_purchase_manager` | Native |
| Purchase User | `purchase.group_purchase_user` | Native |
| Salesperson of the contact | `partner.user_id == self.env.user` | Per-record relationship, not a group |

The implication is one-way: **Sales Manager → Contact Guard Admin**,
never the reverse. Granting Contact Guard Admin alone does not
elevate a user to Sales Manager. This lets administrators assign
Contact Guard Admin to roles outside the sales hierarchy (Account
Manager, Operations Director, etc.) without accidentally elevating
their privileges elsewhere.

### What each role can do

In the table below, *Salesperson* means the user assigned as
salesperson on that specific contact. *SM/CGA* means Sales Manager
or Contact Guard Admin (equivalent for Contact Guard purposes).

| Operation | Internal User | Salesperson of contact | Purchase Manager | Contact Manager | SM / CGA |
|---|---|---|---|---|---|
| See phone/email column in list & kanban | ❌ | ❌ | ❌ | ✅ | ✅ |
| See phone/email on form *(contact has no salesperson)* | ✅ | – | ✅ | ✅ | ✅ |
| See phone/email on form *(contact has salesperson)* | ❌ ¹ | ✅ | ❌ ¹ | ✅ | ✅ |
| First-time fill of phone (was empty) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Edit existing phone *(contact has no salesperson)* | ❌ | ❌ | ✅ | ✅ | ✅ |
| Edit existing phone *(contact has salesperson)* | ❌ | ❌ | ❌ | ✅ | ✅ |
| Set salesperson when **creating** a contact | ✅ | ✅ | ✅ | ✅ | ✅ |
| Change salesperson on existing contact | ❌ | ❌ | ❌ | ❌ | ✅ |
| See Activity Status (form tab + list columns) | ❌ | ❌ | ❌ | ✅ | ✅ |
| Open Contact Guard configuration menu | ❌ | ❌ | ❌ | ❌ | System only |
| Write Contact Guard configuration | ❌ | ❌ | ❌ | ❌ | System only |

> ¹ "Internal User" and "Purchase Manager" do not see the phone/email
> *value* on the form when the contact has an assigned salesperson,
> but the field is hidden via `invisible=` rather than stripped on
> the server. A technically capable user (DevTools, custom RPC) can
> still read the value. List and kanban hiding *is* server-stripped.
> See [View-only hiding on the form](#view-only-hiding-on-the-form-and-its-limit)
> below.

### Enforcement layers

Contact Guard enforces these rules at three different layers, with
different strength:

1. **ORM layer** *(strongest)* — Phone edit protection and
   salesperson change protection are enforced in `res.partner.write`.
   They apply to every code path: web UI, RPC, scripts, automated
   actions. Bypassed only with `env.su`, `import_file` context,
   `suite_skip_phone_check` context, or for public/portal users.
2. **Field-level `groups=`** *(strong)* — Activity Status fields
   (`suite_last_order_date`, `suite_days_since_order`,
   `suite_activity_status`, `suite_has_orders`) carry `groups=` on
   the model. Unauthorized users cannot read them through any
   channel — the ORM strips them from `search_read`, `read`,
   exports, and API calls.
3. **View-level `groups=`** *(strong, view-only)* — List columns,
   kanban card sections, and form pages with `groups=` are removed
   from the view arch on the server before being sent to the client.
   Unauthorized users never receive these elements.

### View-only hiding on the form (and its limit)

Phone and email visibility on the contact **form** is controlled by
an `invisible=` expression rather than `groups=`. This is a deliberate
trade-off: the underlying `phone` and `email` fields are native Odoo
fields without model-level `groups`, and adding model-level `groups`
to them would break compatibility with every other module that
depends on these fields (CRM, Sales, Accounting, WhatsApp, etc.).

The practical consequence:

> A technically capable user (browser DevTools, custom RPC client)
> can still read phone and email values that the form hides via
> `invisible=`. The **list and kanban** views use field-level
> `groups=` and do strip the data on the server, so column-level
> hiding is data-tight; the **form-level** hiding is UI-only.

For most B2B teams this is acceptable — the rule keeps casual
salespeople from browsing each other's contacts in the everyday UI,
which is the realistic threat model. The next section explains why
we did not go further and use record rules to make form hiding
data-tight.

### Why not record rules?

#### What goes wrong

The mainstream way to make salespeople "see only their own contacts"
in Odoo is to add an `ir.rule` on `res.partner` like
`[('user_id', '=', user.id)]`. Almost every paid module on the Apps
Store and most forum answers take this route.

We tried it first and abandoned it. Here is why.

`res.partner` is the central reference hub of Odoo. Users, employees,
companies, bank accounts, followers, journal entries, message
authors, sale order delivery and invoice addresses, supplier info on
products — all of these are partners or join through partners. The
moment you tighten read access on `res.partner` with a record rule,
every place that *implicitly* loads a related partner can fail with
`AccessError`. In practice this surfaces as:

- Salespeople cannot open their own quotations because the SO joins
  `partner_invoice_id` / `partner_shipping_id` and the salesperson
  cannot read those addresses
- Login fails because `res.users` reverse-references the user's own
  partner record
- Chatter, followers, activities, and assignment fields throw
  `Implicitly accessed through 'Users' (res.users)` errors
- Multi-company partners (companion partners of `res.company`)
  become invisible and break warehouse / journal routing

#### What workarounds people try

Existing solutions to these errors are all unpleasant: edit the
built-in `res.partner.rule.private.employee` rule, split internal
users into two parallel groups (one with the rule, one without),
add a chain of `OR` clauses to the record rule for every new
edge case, downgrade `enforce` to read-only so creates do not
break, etc. Every workaround leaks: a future Odoo upgrade, a
new module, or a previously-rare partner reference can resurrect
the access errors. Odoo itself removed the original
`res.partner.rule.private` rule in version 17 because the design
caused too many regressions.

#### Our different stance

Contact Guard takes a different stance. **Contact records stay
fully visible to all internal users.** Sales workflows do not
break. Phone, email, and salesperson are the things you actually
want to protect, and those are gated through field-level `groups=`,
ORM write hooks, and view-level `groups=` (see Enforcement layers
above). The cost of this stance is the form-level `invisible=` on
phone / email being UI-only rather than data-tight, which we
believe is the right cut for most B2B teams: nobody opens DevTools
to scrape a coworker's contacts, but plenty of people accidentally
call a colleague's customer because it showed up in a quick search.

If your security model genuinely requires record-level isolation
of `res.partner` (regulated data, audited environments), Contact
Guard is not the right tool — use record rules and accept the
maintenance burden. For everyone else, this module exists to give
you the 80% solution without the 20% breakage.

---

## Compatibility

- Odoo 19.0 (Community and Enterprise)
- Multi-company aware: every check and configuration is scoped per
  company
- No database-level constraints; all enforcement at the ORM, field,
  or view layer

---

## Installation

### From the Odoo Apps Store

Search for **Contact Guard** in the Apps menu and install. This is
the recommended path.

### From source

```bash
# Clone the SuiteState community modules monorepo (19.0 branch)
git clone -b 19.0 https://github.com/SuiteState/community.git

# Copy or symlink suite_contact_guard into your Odoo addons path
cp -r community/suite_contact_guard /path/to/odoo/addons/

# In Odoo: Apps -> Update Apps List -> search "Contact Guard" -> Install
```

Dependencies (standard Odoo modules):

- `contacts`
- `mail`
- `sales_team`
- `sale`
- `purchase`

---

## License

LGPL-3.0. See the LICENSE file for details.

---

## About

This module is part of the SuiteState community modules collection:
<https://github.com/SuiteState/community>.

Contact: <https://suitestate.com>
