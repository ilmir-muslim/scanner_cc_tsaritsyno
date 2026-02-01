import jsQR from 'jsqr'

export const decodeQRCode = (imageData) => {
    try {
        if (!imageData || !imageData.data || !imageData.width || !imageData.height) {
            console.warn('Invalid image data for QR decoding')
            return null
        }

        const code = jsQR(
            imageData.data,
            imageData.width,
            imageData.height,
            {
                inversionAttempts: "attemptBoth",
                canOverwriteImage: false
            }
        )

        if (code) {
            console.log('QR Code detected:', code.data)
            return code.data
        }
        return null
    } catch (error) {
        console.error('QR decoding error:', error)
        return null
    }
}

// Новая функция для работы с video элементами
export const decodeQRFromVideo = async (videoElement) => {
    return new Promise((resolve) => {
        try {
            const canvas = document.createElement('canvas')
            const context = canvas.getContext('2d')

            if (!videoElement || videoElement.readyState < 2) {
                resolve(null)
                return
            }

            canvas.width = videoElement.videoWidth
            canvas.height = videoElement.videoHeight

            if (canvas.width === 0 || canvas.height === 0) {
                resolve(null)
                return
            }

            context.drawImage(videoElement, 0, 0, canvas.width, canvas.height)
            const imageData = context.getImageData(0, 0, canvas.width, canvas.height)

            const qrCode = decodeQRCode(imageData)
            resolve(qrCode)

        } catch (error) {
            console.error('Video QR decoding error:', error)
            resolve(null)
        }
    })
}