#!/usr/bin/env python3
"""Generates 03-demo-appointments.sql: demo workflow, appointment forms and bookings.

Usage: python3 03-demo-appointments.py 03-demo-appointments.sql (Python 3, no dependency)
See "Changing the demo data set" in the demo README.
Edit the forms, the bookings or the mails here, then regenerate. Demo only: never copy it to
the ops repo, which targets production.
"""
import sys
import unicodedata

OUT = sys.argv[1]

# ---------------------------------------------------------------- workflow
WF = 2
ST_UPCOMING, ST_HONOURED, ST_ABSENT, ST_CANCELLED = 3, 4, 5, 6
AC_CONFIRM, AC_HONOURED, AC_ABSENT, AC_CANCEL = 2, 3, 4, 5
SENDER_NAME = 'CiteLibre - Rendez-vous'
SENDER_EMAIL = 'no-reply@citelibre.org'

MAILS = {
    # id_task: (action, subject, message)
    3: (AC_CONFIRM, 'Confirmation de votre rendez-vous ${reference}',
        '<p>Bonjour ${firstName} ${lastName},</p>'
        '<p>Votre rendez-vous du <strong>${date_appointment} à ${time_appointment}</strong> est confirmé.</p>'
        '<p>Référence : <strong>${reference}</strong></p>${recap!}'
        '<p>Un empêchement ? <a href="${url_cancel}">Annulez votre rendez-vous</a> pour libérer le créneau.</p>'
        '<p>À bientôt,<br/>Le service accueil</p>'),
    4: (AC_HONOURED, 'Merci de votre visite',
        '<p>Bonjour ${firstName} ${lastName},</p>'
        '<p>Merci d\'être venu(e) à votre rendez-vous du ${date_appointment} à ${time_appointment}.</p>'
        '<p>N\'hésitez pas à prendre un nouveau rendez-vous en ligne si besoin.</p>'
        '<p>Le service accueil</p>'),
    5: (AC_ABSENT, 'Rendez-vous manqué',
        '<p>Bonjour ${firstName} ${lastName},</p>'
        '<p>Nous ne vous avons pas vu à votre rendez-vous du ${date_appointment} à ${time_appointment} (référence ${reference}).</p>'
        '<p>Vous pouvez reprendre un rendez-vous en ligne à tout moment.</p>'
        '<p>Le service accueil</p>'),
    7: (AC_CANCEL, 'Annulation de votre rendez-vous ${reference}',
        '<p>Bonjour ${firstName} ${lastName},</p>'
        '<p>Votre rendez-vous du ${date_appointment} à ${time_appointment} (référence ${reference}) est annulé.</p>'
        '<p>Vous pouvez reprendre un rendez-vous en ligne à tout moment.</p>'
        '<p>Le service accueil</p>'),
}
# change status task of the cancel action (no action icons: the BO list builds a broken relative URL for them)
TASK_CANCEL_STATUS = 6

# ---------------------------------------------------------------- forms
MON, TUE, WED, THU, FRI = range(5)
FORMS = [
    dict(id=1, title='Passeport et carte nationale d\'identité', ref='ID',
         description='Dépôt et retrait des demandes de passeport et de carte nationale d\'identité au guichet de l\'état civil.',
         rule='Horaires du guichet état civil', days=[MON, TUE, WED, THU, FRI],
         start='09:00', end='17:00', closed=[('12:00', '13:40')], duration=20, capacity=1, color='#1A73E8'),
    dict(id=2, title='Permanence logement', ref='LOG',
         description='Entretien avec un conseiller logement : demande de logement social, aides au logement, accompagnement.',
         rule='Permanences du mardi et du jeudi', days=[TUE, THU],
         start='14:00', end='17:00', closed=[], duration=30, capacity=1, color='#E8711A'),
    dict(id=3, title='Inscriptions scolaires et périscolaires', ref='SCO',
         description='Inscription à l\'école, à la cantine et aux activités périscolaires. Deux familles sont reçues en même temps.',
         rule='Matinées d\'inscription', days=[MON, WED, FRI],
         start='08:30', end='12:00', closed=[], duration=30, capacity=2, color='#2E9E44'),
]
FORM = {f['id']: f for f in FORMS}

# ---------------------------------------------------------------- bookings
# (form, weekday, week: 1 = next occurrence after today, -1 = last one before today, time, first, last, state)
U, H, A, C = ST_UPCOMING, ST_HONOURED, ST_ABSENT, ST_CANCELLED
BOOKINGS = [
    (1, MON, 1, '09:00', 'Claire', 'Martin', U), (1, MON, 1, '09:40', 'Thomas', 'Bernard', U),
    (1, MON, 1, '10:20', 'Sophie', 'Dubois', U), (1, MON, 1, '14:00', 'Nicolas', 'Petit', U),
    (1, TUE, 1, '09:20', 'Camille', 'Durand', U), (1, TUE, 1, '11:00', 'Julien', 'Leroy', U),
    (1, TUE, 1, '15:20', 'Émilie', 'Moreau', U), (1, WED, 1, '09:00', 'Antoine', 'Simon', U),
    (1, WED, 1, '10:40', 'Léa', 'Laurent', C), (1, WED, 1, '13:40', 'Maxime', 'Lefebvre', U),
    (1, WED, 1, '16:00', 'Manon', 'Michel', U), (1, THU, 1, '10:00', 'Hugo', 'Garcia', U),
    (1, THU, 1, '14:20', 'Chloé', 'David', U), (1, FRI, 1, '09:40', 'Lucas', 'Bertrand', U),
    (1, FRI, 1, '11:20', 'Inès', 'Roux', U), (1, MON, 2, '09:00', 'Karim', 'Benali', U),
    (1, MON, 2, '10:00', 'Fatou', 'Diallo', U), (1, TUE, 2, '14:40', 'Yann', 'Le Gall', U),
    (1, WED, 2, '11:40', 'Mélanie', 'Fournier', U), (1, THU, 2, '09:20', 'Romain', 'Girard', U),
    (1, FRI, 2, '15:00', 'Sarah', 'Bonnet', U),
    (1, MON, -1, '09:00', 'Mehdi', 'Haddad', H), (1, TUE, -1, '10:20', 'Pauline', 'Dupuis', A),
    (1, THU, -1, '14:00', 'Kevin', 'Lambert', H), (1, FRI, -1, '09:40', 'Aïcha', 'Traoré', H),
    (2, TUE, 1, '14:00', 'Olivier', 'Fontaine', U), (2, TUE, 1, '15:00', 'Nathalie', 'Rousseau', U),
    (2, THU, 1, '14:30', 'Mathieu', 'Vincent', U), (2, THU, 1, '16:30', 'Julie', 'Muller', U),
    (2, TUE, 2, '15:30', 'Paul', 'Lefèvre', U), (2, THU, -1, '14:00', 'Céline', 'Faure', H),
    (3, MON, 1, '08:30', 'Samuel', 'Mercier', U), (3, MON, 1, '08:30', 'Anaïs', 'Blanc', U),
    (3, MON, 1, '09:00', 'Vincent', 'Guérin', U), (3, WED, 1, '10:00', 'Laura', 'Chevalier', U),
    (3, WED, 1, '10:30', 'Mamadou', 'Sow', U), (3, FRI, 1, '11:00', 'Élodie', 'Perrin', U),
    (3, MON, 2, '09:30', 'Benjamin', 'Morel', U), (3, WED, -1, '09:00', 'Sandrine', 'Gauthier', A),
]


def ascii_slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return s.lower().replace(' ', '').replace('\'', '')


def q(s):
    return "'" + s.replace('\\', '\\\\').replace("'", "''") + "'"


def minutes(t):
    h, m = t.split(':')
    return int(h) * 60 + int(m)


def hhmm(n):
    return f'{n // 60:02d}:{n % 60:02d}'


def check_booking(b):
    form = FORM[b[0]]
    t = minutes(b[3])
    assert b[1] in form['days'], b
    assert minutes(form['start']) <= t <= minutes(form['end']) - form['duration'], b
    assert (t - minutes(form['start'])) % form['duration'] == 0, b
    assert not any(minutes(c0) <= t < minutes(c1) for c0, c1 in form['closed']), b


out = []
w = out.append
w(f"""-- CiteLibre RendezVous demo data: an appointment workflow that sends emails (caught by
-- Mailpit), three appointment forms and bookings by fictitious users.
-- Generated by 03-demo-appointments.py (edit it, not this file), run after 00-init.sql.
-- Every date is computed from the import day (CURDATE()), so the data set stays current
-- whatever the day the demo is (re)initialized:
-- a booking is "the n-th <weekday> after today" (week > 0) or "before today" (week < 0).

SET NAMES utf8mb4;
SET @today = CURDATE();
SET @start = @today - INTERVAL 2 MONTH;

-- ------------------------------------------------------------------ workflow
INSERT INTO workflow_workflow (id_workflow, name, description, creation_date, is_enabled, workgroup_key, uid_workflow) VALUES
({WF}, 'Rendez-vous', 'Suivi des rendez-vous : confirmation, venue, absence ou annulation, avec un mail à l''usager à chaque étape.', NOW(), 1, 'all', UUID());

INSERT INTO workflow_state (id_state, name, description, id_workflow, is_initial_state, is_required_workgroup_assigned, id_icon, display_order, uid_state) VALUES
({ST_UPCOMING}, 'À venir', 'Rendez-vous confirmé, en attente de la venue de l''usager', {WF}, 1, 0, NULL, 1, UUID()),
({ST_HONOURED}, 'Honoré', 'L''usager est venu au rendez-vous', {WF}, 0, 0, NULL, 2, UUID()),
({ST_ABSENT}, 'Absent', 'L''usager ne s''est pas présenté', {WF}, 0, 0, NULL, 3, UUID()),
({ST_CANCELLED}, 'Annulé', 'Rendez-vous annulé par l''usager ou par un agent', {WF}, 0, 0, NULL, 4, UUID());

-- Confirmation: automatic reflexive action of the initial state, run when the appointment is created
INSERT INTO workflow_action (id_action, name, description, id_workflow, id_state_after, id_alternative_state_after, id_icon, is_automatic, is_mass_action, display_order, is_automatic_reflexive_action, uid_action) VALUES
({AC_CONFIRM}, 'Confirmation', 'Envoi du mail de confirmation à la création du rendez-vous', {WF}, {ST_UPCOMING}, -1, NULL, 0, 0, 1, 1, UUID()),
({AC_HONOURED}, 'Rendez-vous honoré', 'L''usager est venu : envoi d''un mail de remerciement', {WF}, {ST_HONOURED}, -1, NULL, 0, 1, 2, 0, UUID()),
({AC_ABSENT}, 'Usager absent', 'L''usager ne s''est pas présenté : envoi d''un mail l''invitant à reprendre rendez-vous', {WF}, {ST_ABSENT}, -1, NULL, 0, 1, 3, 0, UUID()),
({AC_CANCEL}, 'Annuler le rendez-vous', 'Libère le créneau et envoie un mail d''annulation (aussi déclenchée par le lien d''annulation du mail de confirmation)', {WF}, {ST_CANCELLED}, -1, NULL, 0, 0, 4, 0, UUID());

INSERT INTO workflow_action_state_before (id_action, id_state_before) VALUES
({AC_CONFIRM}, {ST_UPCOMING}), ({AC_HONOURED}, {ST_UPCOMING}), ({AC_ABSENT}, {ST_UPCOMING}), ({AC_CANCEL}, {ST_UPCOMING});

INSERT INTO workflow_task (id_task, task_type_key, id_action, display_order, uid_task) VALUES
(3, 'taskNotifyAppointment', {AC_CONFIRM}, 1, UUID()),
(4, 'taskNotifyAppointment', {AC_HONOURED}, 1, UUID()),
(5, 'taskNotifyAppointment', {AC_ABSENT}, 1, UUID()),
({TASK_CANCEL_STATUS}, 'taskChangeAppointmentStatus', {AC_CANCEL}, 1, UUID()),
(7, 'taskNotifyAppointment', {AC_CANCEL}, 2, UUID());

-- appointment_status 0: unreserved (the appointment is cancelled and its slot freed)
INSERT INTO workflow_task_change_appointment_status_cf (id_task, appointment_status) VALUES ({TASK_CANCEL_STATUS}, 0);

-- id_action_cancel: action run by the cancel link of the mails (${{url_cancel}})
INSERT INTO workflow_task_notify_appointment_cf (id_task, sender_name, sender_email, subject, message, recipients_cc, recipients_bcc, id_action_cancel, ical_notification, create_notif, location, is_sms) VALUES""")
rows = []
for id_task, (action, subject, message) in MAILS.items():
    rows.append(f"({id_task}, {q(SENDER_NAME)}, {q(SENDER_EMAIL)}, {q(subject)}, {q(message)}, '', '', {AC_CANCEL}, 0, 0, '', 0)")
w(',\n'.join(rows) + ';\n')

w('-- ------------------------------------------------------------------ appointment forms')
w('INSERT INTO appointment_form (id_form, title, description, reference, id_category, starting_validity_date, ending_validity_date, is_active, id_workflow, workgroup, is_multislot_appointment, role_fo, capacity_per_slot, nb_consecutive_slots, is_anonymizable, anonymization_pattern) VALUES')
w(',\n'.join(f"({f['id']}, {q(f['title'])}, {q(f['description'])}, {q(f['ref'])}, NULL, @start, NULL, 1, {WF}, 'all', 0, 'none', 1, 1, 0, '')" for f in FORMS) + ';\n')
w('INSERT INTO appointment_display (id_display, display_title_fo, icon_form_content, icon_form_mime_type, nb_weeks_to_display, is_displayed_on_portlet, id_calendar_template, id_form) VALUES')
w(',\n'.join(f"({f['id']}, 1, '', '', 4, 1, 2, {f['id']})" for f in FORMS) + ';\n')
w('INSERT INTO appointment_localization (id_localization, longitude, latitude, address, id_form) VALUES')
w(',\n'.join(f"({f['id']}, NULL, NULL, 'Hôtel de ville, 1 place de la Mairie', {f['id']})" for f in FORMS) + ';\n')
w('-- mandatory email: the workflow mails need it')
w('INSERT INTO appointment_form_rule (id_form_rule, is_captcha_enabled, is_mandatory_email_enabled, is_active_authentication, nb_days_before_new_appointment, min_time_before_appointment, nb_max_appointments_per_user, nb_days_for_max_appointments_per_user, bo_overbooking, id_form) VALUES')
w(',\n'.join(f"({f['id']}, 0, 1, 0, 0, 0, 0, 0, 0, {f['id']})" for f in FORMS) + ';\n')
w('INSERT INTO appointment_form_message (id_form_message, calendar_title, field_firstname_title, field_firstname_help, field_lastname_title, field_lastname_help, field_email_title, field_email_help, field_confirmationEmail_title, field_confirmationEmail_help, text_appointment_created, url_redirect_after_creation, text_appointment_canceled, label_button_redirection, no_available_slot, calendar_description, calendar_reserve_label, calendar_full_label, id_form) VALUES')
w(',\n'.join(f"({f['id']}, 'Choisir une date', 'Prénom', '', 'Nom', '', 'Email', '', 'Confirmation Email', '', 'Votre demande de rendez-vous a bien été créée avec la référence %%REF%%. Un mail de confirmation vous a été envoyé.', 'jsp/site/Portal.jsp', 'Votre demande de rendez-vous a bien été annulée', 'Terminer', 'Aucun créneau disponible n''a été trouvé. Veuillez réitérer votre recherche ultérieurement.', '', 'Réserver', 'Complet', {f['id']})" for f in FORMS) + ';\n')

w('INSERT INTO appointment_reservation_rule (id_reservation_rule, name, description, color, enable, max_capacity_per_slot, max_people_per_appointment, duration_appointments, id_form) VALUES')
w(',\n'.join(f"({f['id']}, {q(f['rule'])}, {q(f['rule'])}, {q(f['color'])}, 1, {f['capacity']}, 1, {f['duration']}, {f['id']})" for f in FORMS) + ';\n')
w('INSERT INTO appointment_week_definition (id_week_definition, id_reservation_rule, date_of_apply, ending_date_of_apply) VALUES')
w(',\n'.join(f"({f['id']}, {f['id']}, @start, @today + INTERVAL 1 YEAR)" for f in FORMS) + ';\n')

working_days, time_slots = [], []
id_wd = id_ts = 0
for f in FORMS:
    for day in f['days']:
        id_wd += 1
        working_days.append(f"({id_wd}, {day + 1}, {f['id']})")
        for t in range(minutes(f['start']), minutes(f['end']) - f['duration'] + 1, f['duration']):
            id_ts += 1
            is_open = 0 if any(minutes(c0) <= t < minutes(c1) for c0, c1 in f['closed']) else 1
            time_slots.append(f"({id_ts}, '{hhmm(t)}:00', '{hhmm(t + f['duration'])}:00', {is_open}, {f['capacity']}, {id_wd})")
w('-- day_of_week: 1 = Monday ... 7 = Sunday')
w('INSERT INTO appointment_working_day (id_working_day, day_of_week, id_reservation_rule) VALUES')
w(',\n'.join(working_days) + ';\n')
w('INSERT INTO appointment_time_slot (id_time_slot, starting_time, ending_time, is_open, max_capacity, id_working_day) VALUES')
w(',\n'.join(time_slots) + ';\n')

# slots: one per booked (form, weekday, week, time)
slots = {}
for b in BOOKINGS:
    check_booking(b)
    key = b[:4]
    slots.setdefault(key, {'id': len(slots) + 1, 'taken': 0})
    if b[6] != C:
        slots[key]['taken'] += 1
for key, s in slots.items():
    assert s['taken'] <= FORM[key[0]]['capacity'], key

w(f"""-- ------------------------------------------------------------------ bookings
-- weekday: 0 = Monday ... 4 = Friday
CREATE TEMPORARY TABLE demo_slot (id_slot INT PRIMARY KEY, id_form INT, weekday INT, week INT, slot_time TIME, duration INT, capacity INT, taken INT, slot_date DATE);
INSERT INTO demo_slot (id_slot, id_form, weekday, week, slot_time, duration, capacity, taken) VALUES""")
w(',\n'.join(f"({s['id']}, {k[0]}, {k[1]}, {k[2]}, '{k[3]}', {FORM[k[0]]['duration']}, {FORM[k[0]]['capacity']}, {s['taken']})" for k, s in slots.items()) + ';\n')
w("""UPDATE demo_slot SET slot_date = IF(week > 0,
    @today + INTERVAL ((weekday - WEEKDAY(@today) + 6) % 7 + 1 + 7 * (week - 1)) DAY,
    @today - INTERVAL ((WEEKDAY(@today) - weekday + 6) % 7 + 1 + 7 * (-week - 1)) DAY);
""")
w('CREATE TEMPORARY TABLE demo_booking (id INT PRIMARY KEY, id_slot INT, first_name VARCHAR(255), last_name VARCHAR(255), email VARCHAR(255), phone VARCHAR(20), id_state INT);')
w('INSERT INTO demo_booking (id, id_slot, first_name, last_name, email, phone, id_state) VALUES')
rows = []
for i, b in enumerate(BOOKINGS, 1):
    email = f'{ascii_slug(b[4])}.{ascii_slug(b[5])}@example.org'
    phone = f'06 39 98 {i // 100:02d} {i % 100:02d}'
    rows.append(f"({i}, {slots[b[:4]]['id']}, {q(b[4])}, {q(b[5])}, {q(email)}, {q(phone)}, {b[6]})")
w(',\n'.join(rows) + ';\n')

w(f"""INSERT INTO appointment_slot (id_slot, starting_date_time, ending_date_time, is_open, is_specific, max_capacity, nb_remaining_places, nb_potential_remaining_places, nb_places_taken, id_form)
SELECT id_slot, TIMESTAMP(slot_date, slot_time), TIMESTAMP(slot_date, slot_time) + INTERVAL duration MINUTE, 1, 0, capacity, capacity - taken, capacity - taken, taken, id_form
FROM demo_slot;

INSERT INTO appointment_user (id_user, guid, first_name, last_name, email, phone_number)
SELECT id, NULL, first_name, last_name, email, phone FROM demo_booking;

-- reference: form reference + 10 characters, like the plugin (id + hash)
INSERT INTO appointment_appointment (id_appointment, reference, nb_places, is_cancelled, id_action_cancelled, id_action_reported, notification, id_admin_user, date_appointment_create, admin_access_code_create, id_user, is_surbooked)
SELECT b.id, CONCAT(f.reference, LEFT(CONCAT(b.id, SHA2(CONCAT(b.id, b.email), 256)), 10)), 1, b.id_state = {ST_CANCELLED}, {AC_CANCEL}, 0, 0, 0,
       TIMESTAMP(s.slot_date, s.slot_time) - INTERVAL (3 + b.id % 9) DAY, NULL, b.id, 0
FROM demo_booking b JOIN demo_slot s ON s.id_slot = b.id_slot JOIN appointment_form f ON f.id_form = s.id_form;

INSERT INTO appointment_appointment_slot (id_appointment, id_slot, nb_places)
SELECT id, id_slot, 1 FROM demo_booking;

INSERT INTO workflow_resource_workflow (id_resource, resource_type, id_state, id_workflow, id_external_parent, is_associated_workgroups)
SELECT b.id, 'appointment', b.id_state, {WF}, s.id_form, 0 FROM demo_booking b JOIN demo_slot s ON s.id_slot = b.id_slot;

-- history: the automatic confirmation, then the agent action for the past or cancelled ones
INSERT INTO workflow_resource_history (id_resource, resource_type, id_workflow, id_action, creation_date, user_access_code)
SELECT b.id, 'appointment', {WF}, {AC_CONFIRM}, a.date_appointment_create, 'auto'
FROM demo_booking b JOIN appointment_appointment a ON a.id_appointment = b.id;
INSERT INTO workflow_resource_history (id_resource, resource_type, id_workflow, id_action, creation_date, user_access_code)
SELECT b.id, 'appointment', {WF}, CASE b.id_state WHEN {ST_HONOURED} THEN {AC_HONOURED} WHEN {ST_ABSENT} THEN {AC_ABSENT} ELSE {AC_CANCEL} END,
       IF(b.id_state = {ST_CANCELLED}, a.date_appointment_create + INTERVAL 1 DAY, TIMESTAMP(s.slot_date, s.slot_time) + INTERVAL 1 HOUR), 'admin'
FROM demo_booking b JOIN appointment_appointment a ON a.id_appointment = b.id JOIN demo_slot s ON s.id_slot = b.id_slot
WHERE b.id_state <> {ST_UPCOMING};

DROP TEMPORARY TABLE demo_booking;
DROP TEMPORARY TABLE demo_slot;
""")

with open(OUT, 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(out))
print(f'{len(FORMS)} forms, {len(time_slots)} time slots, {len(slots)} slots, {len(BOOKINGS)} bookings -> {OUT}')
