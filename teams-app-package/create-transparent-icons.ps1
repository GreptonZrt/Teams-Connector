# Teams Icon Generator - Transparent Outline
Add-Type -AssemblyName System.Drawing

# Create 32x32 outline icon with TRANSPARENT background
$outlineSize = 32
$outlineBitmap = New-Object System.Drawing.Bitmap($outlineSize, $outlineSize)
$outlineGraphics = [System.Drawing.Graphics]::FromImage($outlineBitmap)

# IMPORTANT: Don't fill background - leave it transparent
$outlineGraphics.Clear([System.Drawing.Color]::Transparent)

# Set high quality rendering
$outlineGraphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$outlineGraphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias

# White color for the letter F
$whiteBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White)
$font = New-Object System.Drawing.Font("Arial", 20, [System.Drawing.FontStyle]::Bold)

# Center the letter
$sf = New-Object System.Drawing.StringFormat
$sf.Alignment = [System.Drawing.StringAlignment]::Center
$sf.LineAlignment = [System.Drawing.StringAlignment]::Center

$rect = New-Object System.Drawing.RectangleF(0, 0, $outlineSize, $outlineSize)
$outlineGraphics.DrawString("F", $font, $whiteBrush, $rect, $sf)

# Save as PNG with transparency
$outlineBitmap.Save("$PSScriptRoot\outline.png", [System.Drawing.Imaging.ImageFormat]::Png)

Write-Host "✅ Transparent outline icon created: outline.png (32x32, transparent background)"

# Create 192x192 color icon
$colorSize = 192
$colorBitmap = New-Object System.Drawing.Bitmap($colorSize, $colorSize)
$colorGraphics = [System.Drawing.Graphics]::FromImage($colorBitmap)

# Blue background (same as before)
$blueBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(96, 161, 142))
$colorGraphics.FillRectangle($blueBrush, 0, 0, $colorSize, $colorSize)

# Set high quality rendering
$colorGraphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$colorGraphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias

# White letter F
$colorFont = New-Object System.Drawing.Font("Arial", 120, [System.Drawing.FontStyle]::Bold)
$colorRect = New-Object System.Drawing.RectangleF(0, 0, $colorSize, $colorSize)
$colorGraphics.DrawString("F", $colorFont, $whiteBrush, $colorRect, $sf)

# Save color icon
$colorBitmap.Save("$PSScriptRoot\color.png", [System.Drawing.Imaging.ImageFormat]::Png)

Write-Host "✅ Color icon created: color.png (192x192)"

# Cleanup
$outlineGraphics.Dispose()
$outlineBitmap.Dispose()
$colorGraphics.Dispose()
$colorBitmap.Dispose()
$whiteBrush.Dispose()
$blueBrush.Dispose()
$font.Dispose()
$colorFont.Dispose()
$sf.Dispose()

Write-Host ""
Write-Host "Icons created successfully!"
Write-Host "- outline.png: 32x32 with TRANSPARENT background (white F)"
Write-Host "- color.png: 192x192 with blue background (white F)"
