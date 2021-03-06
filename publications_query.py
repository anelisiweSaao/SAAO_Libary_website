import collections
import datetime
import io
import json
import os
import re
import smtplib
import subprocess
import xlsxwriter

from email import encoders
from email.message import Message
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config
from ads_queries import ADSQueries


def ignore_tmp_bibcodes(bibcodes):
    """Filter out bibcodes which are temporary.

    Params:
    -------
    bibcodes: list of str
        Bibcodes to filter.

    Returns:
    --------
    list of str
        List of bibcodes lswithout the temporary ones.
    """

    return [bibcode for bibcode in bibcodes if 'tmp' not in bibcode]


def previously_found_bibcodes():
    """Return the list of bibcodes found in previous searches.

    The previously found publications are stored as bibcode in a file, whose path is set as PREVIOUS_BIBCODES_FILE in
    the configuration file. If this file doesn't exist, it is created first. If it cannot be created, an exception is
    raised.

    Returns:
    --------
    list
        List of publications found in a previous search.
    """

    # create the file for storing previously found bibcodes, if need be
    _ensure_previously_recorded_file_exists()

    with open(config.PREVIOUS_BIBCODES_FILE) as f:
        return [line.strip() for line in f.readlines()]


def _ensure_previously_recorded_file_exists():
    """Create the file for storing previously found bibcodes, if it doesn't exist yet.

    If the file cannot be created an exception is raised.
    """

    if not os.path.isfile(config.PREVIOUS_BIBCODES_FILE):
        with open(config.PREVIOUS_BIBCODES_FILE, 'w') as f:
            f.close()

    # check whether the file could be created
    if not os.path.isfile(config.PREVIOUS_BIBCODES_FILE):
        raise IOError('The file for storing previously found bibcodes could not be created: ' +
                      config.PREVIOUS_BIBCODES_FILE)


def publications_spreadsheet(publications, columns):
    """Create a spreadsheet with the publications.

    Params:
    -------
    publications: list
        Publications.
    columns: list of str
        Columns to include in the spreadsheet.

    Returns:
    --------
    io.BytesIO:
        Spreadsheet with the publication details.

    """
    out = io.BytesIO()
    workbook = xlsxwriter.Workbook(out)

    worksheet = workbook.add_worksheet()
    for row, p in enumerate(publications):
        for col, c in enumerate(columns):
            worksheet.write(row, col, p.get(c, ''))

    workbook.close()

    # rewind the buffer
    out.seek(0)

    return out


def spreadsheet_columns():
    """Return an ordered dictionary of the columns for a spreadsheet.

    The dictionary keys are the keys to use for accessing details in a publication dictionary, the values are more
    human-friendly column names.

    Some of the keys may not be included in a publication dictionary.

    Returns:
    --------
    collections.OrderedDict:
        Dictionary of column keys and names.
    """
    columns = collections.OrderedDict()
    columns['record_type'] = 'Record Type'
    columns['publication_number'] = 'Doc/Publication Number'
    columns['author'] = 'Responsibility'
    columns['title'] = 'Title'
    columns['pub'] = 'Journal'
    columns['volume'] = 'Volume'
    columns['issue'] = 'Issue'
    columns['page'] = 'Page'
    columns['refereed'] = 'Refereed'
    columns['bibcode'] = 'Bibcode'
    columns['doi'] = 'DOI'
    columns['ads_url'] = 'ADS URL'
    columns['abstract'] = 'Abstract'
    columns['telescopes'] = 'Telescopes'
    columns['keywords'] = 'Keywords'

    return columns


def send_mails(spreadsheets, columns):
    column_explanation = '\n'.join([chr(ord('A') + i) + ' - ' + columns[key] + '<br>'
                                   for i, key in enumerate(columns.keys())])

    outer = MIMEMultipart()
    outer['Subject'] = 'Publications Query Results'
    outer['To'] = ', '.join(config.LIBRARIAN_EMAIL_ADDRESSES)
    outer['From'] = config.FROM_EMAIL_ADDRESS
    outer.preamble = 'You will not see this in a MIME-aware mail reader.\n'

    body = MIMEMultipart('alternative')
    html = '''<p>Dear Librarian,</p>

<p>Please find attached the results for the publications query.</p>

<p>{column_explanation}</p>

<p>Kind regards,</p>

<p>Your Friendly Publications Query Script</p>'''.format(column_explanation=column_explanation)
    text = re.sub('<[^>]+>', '', html)

    body.attach(MIMEText(text, 'plain'))
    body.attach(MIMEText(html, 'html'))

    outer.attach(body)

    for spreadsheet in spreadsheets:
        msg = MIMEBase('application', 'application/vnd.ms-excel')
        read = spreadsheet['content'].read()
        msg.set_payload(read)
        encoders.encode_base64(msg)
        msg.add_header('Content-Disposition', 'attachment', filename=spreadsheet['name'])
        outer.attach(msg)

    with smtplib.SMTP('smtp.saao.ac.za') as s:
        s.sendmail(config.FROM_EMAIL_ADDRESS, config.LIBRARIAN_EMAIL_ADDRESSES, outer.as_string())


def run_pub(start, end):
    # d = datetime.date(2017, 6, 15)

    queries = ADSQueries(from_date=start, to_date=end)

    by_keywords = queries.by_keywords(config.KEYWORDS)
    by_authors = queries.by_authors(config.AUTHORS.keys())
    #by_affiliations = queries.by_affiliations(config.AFFILIATIONS)

    all = {**by_keywords, **by_authors}#, **by_affiliations}

    # make sure the keywords are present
    for b in by_keywords:
        all[b]['keywords'] = by_keywords[b]['keywords']

    # now that we have collected everything, we can flatten our map to a list
    publications = [all[b] for b in all.keys()]
    publications.sort(key=lambda p: p['bibcode'])

    # add URL to ADS page
    for p in publications:
        p['ads_url'] = 'https://ui.adsabs.harvard.edu/#abs/{0}/abstract'.format(p['bibcode'])

    # add refereed status
    for p in publications:
        p['refereed'] = 'REFEREED' in p['property']

    # make some content more amenable to humans and xslxwriter alike
    for p in publications:
        list_value_columns = ['author', 'title', 'doi', 'keywords', 'page']
        for c in list_value_columns:
            if c in p and p[c]:
                p[c] = ', '.join(p[c])

    columns = spreadsheet_columns()
    send_mails([
        dict(name='all.xlsx', content=publications_spreadsheet(publications, columns.keys()))
    ], columns)
    #gitt
