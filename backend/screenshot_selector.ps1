param(
    [string]$OutputPath = "",
    [string]$SaveDir = ""
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = "WebRPA Screenshot Tool"
$form.FormBorderStyle = 'None'
$form.WindowState = 'Maximized'
$form.TopMost = $true
$form.Cursor = [System.Windows.Forms.Cursors]::Cross
$form.BackColor = [System.Drawing.Color]::Black
$form.Opacity = 0.3

$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$screenWidth = $screen.Width
$screenHeight = $screen.Height

$screenshot = New-Object System.Drawing.Bitmap($screenWidth, $screenHeight)
$graphics = [System.Drawing.Graphics]::FromImage($screenshot)
$graphics.CopyFromScreen(0, 0, 0, 0, $screenshot.Size)

$pictureBox = New-Object System.Windows.Forms.PictureBox
$pictureBox.Image = $screenshot
$pictureBox.SizeMode = 'AutoSize'
$pictureBox.Location = New-Object System.Drawing.Point(0, 0)
$form.Controls.Add($pictureBox)

$script:startX = 0
$script:startY = 0
$script:endX = 0
$script:endY = 0
$script:isSelecting = $false
$script:selectedImage = $null
$script:cancelled = $false

$pictureBox.Add_MouseDown({
    param($sender, $e)
    $script:startX = $e.X
    $script:startY = $e.Y
    $script:isSelecting = $true
})

$pictureBox.Add_MouseMove({
    param($sender, $e)
    if ($script:isSelecting) {
        $script:endX = $e.X
        $script:endY = $e.Y
        $pictureBox.Refresh()
    }
})

$pictureBox.Add_MouseUp({
    param($sender, $e)
    $script:endX = $e.X
    $script:endY = $e.Y
    $script:isSelecting = $false
    
    $x1 = [Math]::Min($script:startX, $script:endX)
    $y1 = [Math]::Min($script:startY, $script:endY)
    $x2 = [Math]::Max($script:startX, $script:endX)
    $y2 = [Math]::Max($script:startY, $script:endY)
    $width = $x2 - $x1
    $height = $y2 - $y1
    
    if ($width -gt 10 -and $height -gt 10) {
        $script:selectedImage = New-Object System.Drawing.Bitmap($width, $height)
        $g = [System.Drawing.Graphics]::FromImage($script:selectedImage)
        $g.DrawImage($screenshot, 0, 0, (New-Object System.Drawing.Rectangle($x1, $y1, $width, $height)), [System.Drawing.GraphicsUnit]::Pixel)
        $g.Dispose()
        
        $form.Close()
    }
})

$pictureBox.Add_Paint({
    param($sender, $e)
    if ($script:isSelecting) {
        $x1 = [Math]::Min($script:startX, $script:endX)
        $y1 = [Math]::Min($script:startY, $script:endY)
        $width = [Math]::Abs($script:endX - $script:startX)
        $height = [Math]::Abs($script:endY - $script:startY)
        
        $pen = New-Object System.Drawing.Pen([System.Drawing.Color]::Red, 2)
        $e.Graphics.DrawRectangle($pen, $x1, $y1, $width, $height)
        
        $text = "$width x $height"
        $font = New-Object System.Drawing.Font("Arial", 12, [System.Drawing.FontStyle]::Bold)
        $brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::Red)
        $e.Graphics.DrawString($text, $font, $brush, $x1, $y1 - 20)
        
        $pen.Dispose()
        $font.Dispose()
        $brush.Dispose()
    }
})

$form.Add_KeyDown({
    param($sender, $e)
    if ($e.KeyCode -eq 'Escape') {
        $script:cancelled = $true
        $form.Close()
    }
})

[void]$form.ShowDialog()

$graphics.Dispose()
$form.Dispose()

if (-not $script:cancelled -and $script:selectedImage) {
    if ($OutputPath) {
        $savePath = $OutputPath
    } elseif ($SaveDir) {
        $guid = [guid]::NewGuid().ToString()
        $savePath = Join-Path $SaveDir "$guid.png"
    } else {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $savePath = "screenshot_$timestamp.png"
    }
    
    $script:selectedImage.Save($savePath, [System.Drawing.Imaging.ImageFormat]::Png)
    $script:selectedImage.Dispose()
    
    $jsonResult = "{`"success`":true,`"path`":`"$($savePath.Replace('\','\\'))`",`"message`":`"Screenshot saved`"}"
    [Console]::WriteLine($jsonResult)
    exit 0
} else {
    if ($script:selectedImage) {
        $script:selectedImage.Dispose()
    }
    
    $jsonResult = "{`"success`":false,`"error`":`"User cancelled`"}"
    [Console]::WriteLine($jsonResult)
    exit 1
}
