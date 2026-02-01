
export const testBrowserPrint = () => {
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head><title>Test Print</title></head>
        <body>
            <h1>Test Print</h1>
            <script>window.print(); window.close();</script>
        </body>
        </html>
    `);
    printWindow.document.close();
};
