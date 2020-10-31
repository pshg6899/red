import glob
from PyPDF2 import PdfFileWriter, PdfFileReader


def merger(file_list_path: object,  output_merge_file: object) -> object:
    """
    
    :rtype: object
    """
    pdf_writer = PdfFileWriter()

    for path in file_list_path:
        pdf_reader = pdfFileReader(path)
        for page in range(pdf_reader.getNumPages()):
            # Add each page to the writer object
            pdf_writer.addpage(pdf_reader.getPage(page))

    # Write out the merged PDF
    with open(output_merge_file, 'wb') as out:
        pdf_writer.write(out)
