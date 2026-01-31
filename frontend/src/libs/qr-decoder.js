import jsQR from 'jsqr'

export const decodeQRCode = (imageData) => {
    try {
        const code = jsQR(
            imageData.data,
            imageData.width,
            imageData.height,
            {
                inversionAttempts: "dontInvert",
            }
        )
        return code ? code.data : null
    } catch (error) {
        console.error('QR decoding error:', error)
        return null
    }
}