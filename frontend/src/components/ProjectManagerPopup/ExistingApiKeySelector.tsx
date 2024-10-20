import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ApiKey } from '@/lib/types';
import { renderCompactApiKeyInfo } from '@/lib/apiKeyUtils'
import { AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogFooter, AlertDialogCancel, AlertDialogAction } from "@/components/ui/alert-dialog";
import { Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface ExistingApiKeySelectorProps {
  existingApiKeys: ApiKey[];
  selectedApiKeyId: number | null;
  onApiKeySelect: (keyId: string) => void;
  onRemoveApiKey: (keyId: number) => Promise<void>;
}

const ExistingApiKeySelector: React.FC<ExistingApiKeySelectorProps> = ({
  existingApiKeys,
  selectedApiKeyId,
  onApiKeySelect,
  onRemoveApiKey
}) => {
  return (
    <div className="space-y-2">
      <div className="flex items-center space-x-2">
        <Select 
          onValueChange={onApiKeySelect} 
          value={selectedApiKeyId?.toString() || "default"}
          className="flex-grow"
        >
          <SelectTrigger className="w-full mt-4">
            <SelectValue placeholder="Select existing API Key">
              {selectedApiKeyId 
                ? renderCompactApiKeyInfo(existingApiKeys.find(key => key.id === selectedApiKeyId)!)
                : "Select existing API Key"}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="default" disabled>Select existing API Key</SelectItem>
            {existingApiKeys.map(key => (
              <SelectItem key={key.id} value={key.id.toString()} className="py-2">
                <div className="flex flex-col space-y-1">
                  {renderCompactApiKeyInfo(key)}
                  <div className="text-sm text-muted-foreground">{key.domain_email}</div>
                  <div className="text-xs text-muted-foreground">
                    {key.api_key.substring(0, 20)}...
                  </div>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        
        {selectedApiKeyId && (
          <div className="flex items-center h-[42px] mt-4">
            <AlertDialog>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <AlertDialogTrigger asChild>
                      <Button 
                        size="icon" 
                        variant="ghost" 
                        className="rounded-full group flex items-center justify-center h-9 w-9"
                      >
                        <Trash2 className="w-4 h-4 text-destructive group-hover:text-destructive-foreground" />
                      </Button>
                    </AlertDialogTrigger>
                  </TooltipTrigger>
                  <TooltipContent className="bg-primaryAccent text-primaryAccent-foreground">
                    <p>Delete API Key</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This action cannot be undone. This will permanently delete the API key and remove all associated data.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={() => selectedApiKeyId && onRemoveApiKey(selectedApiKeyId)}
                    className="text-destructive-foreground hover:bg-primaryAccent"
                  >
                    Delete
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExistingApiKeySelector;
