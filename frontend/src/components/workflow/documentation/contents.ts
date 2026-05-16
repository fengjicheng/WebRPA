import { gettingStartedContent } from './content-getting-started'
import { basicModulesContent } from './content-basic'
import { dataProcessingContent } from './content-data'
import { advancedFeaturesContent } from './content-advanced'
import { selectorGuideContent } from './content-selector'
import { practicalCasesContent } from './content-cases'
import { workflowPatternsContent } from './content-patterns'
import { tipsTricksContent } from './content-tips'
import { browserGuideContent } from './content-browser'
import { excelGuideContent } from './content-excel'
import { variablesGuideContent } from './content-variables'
import { debugGuideContent } from './content-debug'
import { notificationsGuideContent } from './content-notifications'
import { databaseGuideContent } from './content-database'
import { mediaGuideContent } from './content-media'
import { filesGuideContent } from './content-files'
import { pdfGuideContent } from './content-pdf'
import { triggersGuideContent } from './content-triggers'
import { scheduledTasksGuideContent } from './content-scheduled-tasks'
import { customModulesGuideContent } from './content-custom-modules'
import { phoneGuideContent } from './content-phone'
import { testReportContent } from './content-test-report'
import { desktopGuideContent } from './content-desktop'
import { notifyGuideContent } from './content-notify'
import { sshGuideContent } from './content-ssh'
import { networkGuideContent } from './content-network'
import { botsGuideContent } from './content-bots'
import { inputGuideContent } from './content-input'
import { imageGuideContent } from './content-image'
import { utilsGuideContent } from './content-utils'
import { mathFlowGuideContent } from './content-math-flow'
import { aiVisionGuideContent } from './content-ai-vision'
import { shareGuideContent } from './content-share'
import { sapGuideContent } from './content-sap'
import { feishuGuideContent } from './content-feishu'

export const documentContents: Record<string, string> = {
  'getting-started': gettingStartedContent,
  'browser-guide': browserGuideContent,
  'basic-modules': basicModulesContent,
  'variables-guide': variablesGuideContent,
  'data-processing': dataProcessingContent,
  'math-flow-guide': mathFlowGuideContent,
  'excel-guide': excelGuideContent,
  'database-guide': databaseGuideContent,
  'network-guide': networkGuideContent,
  'triggers-guide': triggersGuideContent,
  'scheduled-tasks-guide': scheduledTasksGuideContent,
  'custom-modules-guide': customModulesGuideContent,
  'advanced-features': advancedFeaturesContent,
  'ai-vision-guide': aiVisionGuideContent,
  'desktop-guide': desktopGuideContent,
  'input-guide': inputGuideContent,
  'image-guide': imageGuideContent,
  'files-guide': filesGuideContent,
  'pdf-guide': pdfGuideContent,
  'media-guide': mediaGuideContent,
  'phone-guide': phoneGuideContent,
  'bots-guide': botsGuideContent,
  'notify-guide': notifyGuideContent,
  'ssh-guide': sshGuideContent,
  'share-guide': shareGuideContent,
  'utils-guide': utilsGuideContent,
  'test-report-guide': testReportContent,
  'sap-guide': sapGuideContent,
  'feishu-guide': feishuGuideContent,
  'selector-guide': selectorGuideContent,
  'notifications-guide': notificationsGuideContent,
  'debug-guide': debugGuideContent,
  'practical-cases': practicalCasesContent,
  'workflow-patterns': workflowPatternsContent,
  'tips-tricks': tipsTricksContent,
}
